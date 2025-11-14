"""
SageMaker Client for Dashboard Predictions
Handles real-time predictions from deployed SageMaker models
"""

import boto3
import json
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SageMakerPredictor:
    """Client for making predictions using SageMaker endpoints"""

    def __init__(self, endpoint_name=None):
        """
        Initialize SageMaker client

        Args:
            endpoint_name: Name of the SageMaker endpoint
        """
        self.endpoint_name = endpoint_name or os.environ.get('SAGEMAKER_ENDPOINT_NAME')
        self.runtime = None  # Lazy initialization
        self._region = os.environ.get('AWS_REGION', 'us-east-1')
        logger.info(f"Initialized SageMaker client with endpoint: {self.endpoint_name}")

    def _get_runtime_client(self):
        """Lazy initialization of boto3 runtime client"""
        if self.runtime is None:
            try:
                self.runtime = boto3.client('sagemaker-runtime', region_name=self._region)
                logger.info(f"Created SageMaker runtime client in region: {self._region}")
            except Exception as e:
                logger.error(f"Failed to create SageMaker runtime client: {str(e)}")
                raise
        return self.runtime

    def predict_delinquencies(self, historical_data, periods_ahead=12):
        """
        Predict future delinquency rates

        Args:
            historical_data: DataFrame with historical delinquency data
            periods_ahead: Number of future periods to predict

        Returns:
            DataFrame with predictions for different delinquency categories
        """
        logger.info(f"Predicting delinquencies for {periods_ahead} periods ahead")

        try:
            # If endpoint is configured, use SageMaker for predictions
            if self.endpoint_name:
                return self._predict_with_sagemaker(historical_data, periods_ahead)
            else:
                logger.warning("No SageMaker endpoint configured, using local prediction model")
                return self._predict_local(historical_data, periods_ahead)

        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            # Fallback to local predictions
            return self._predict_local(historical_data, periods_ahead)

    def _predict_with_sagemaker(self, historical_data, periods_ahead):
        """Make predictions using SageMaker endpoint"""
        predictions = []

        # Get the last known values
        last_row = historical_data.iloc[-1]

        # For each future period
        for i in range(1, periods_ahead + 1):
            # Prepare features for prediction
            features = self._prepare_features(historical_data, last_row, i)

            # Call SageMaker endpoint
            payload = {
                'instances': [features]
            }

            response = self._get_runtime_client().invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='application/json',
                Body=json.dumps(payload)
            )

            # Parse response
            result = json.loads(response['Body'].read().decode())
            predictions.append(result['predictions'][0])

        # Convert to DataFrame
        return self._format_predictions(historical_data, predictions, periods_ahead)

    def _predict_local(self, historical_data, periods_ahead):
        """
        Generate predictions using a simple time-series forecasting model
        This is a fallback when SageMaker endpoint is not available
        """
        logger.info("Using local prediction model")

        # Get historical trends
        recent_data = historical_data.tail(12)  # Last 12 periods

        # Calculate trends for each delinquency category
        categories = ['30_days', '60_days', '90_plus_days']
        predictions = []

        for i in range(1, periods_ahead + 1):
            pred = {'period': i}

            for category in categories:
                col_name = f'delinquency_{category}'
                if col_name in recent_data.columns:
                    # Simple exponential smoothing with trend
                    values = recent_data[col_name].values
                    alpha = 0.3  # Smoothing factor
                    beta = 0.1   # Trend factor

                    # Calculate trend
                    trend = np.polyfit(range(len(values)), values, 1)[0]

                    # Last smoothed value
                    last_value = values[-1]

                    # Predict next value with trend and some noise
                    predicted_value = last_value + (trend * i) + np.random.normal(0, 0.001)

                    # Ensure values stay in reasonable range (0-1 for rates)
                    predicted_value = max(0, min(1, predicted_value))

                    pred[col_name] = predicted_value
                else:
                    pred[col_name] = 0.02  # Default value

            # Add confidence intervals
            pred['confidence_lower'] = 0.8
            pred['confidence_upper'] = 1.2

            predictions.append(pred)

        return self._format_predictions(historical_data, predictions, periods_ahead)

    def _prepare_features(self, historical_data, last_row, period_ahead):
        """
        Prepare features for SageMaker prediction

        Args:
            historical_data: Historical data DataFrame
            last_row: Last row of historical data
            period_ahead: Number of periods ahead to predict

        Returns:
            List of feature values
        """
        # Extract relevant features
        features = [
            last_row.get('delinquency_30_days', 0.02),
            last_row.get('delinquency_60_days', 0.01),
            last_row.get('delinquency_90_plus_days', 0.005),
            last_row.get('cumulative_default_rate', 0.01),
            last_row.get('cumulative_loss_rate', 0.008),
            last_row.get('weighted_average_fico', 700),
            last_row.get('weighted_average_ltv', 0.75),
            last_row.get('weighted_average_dti', 0.35),
            last_row.get('pool_balance_ratio', 0.85),
            last_row.get('pool_seasoning_months', 24),
            last_row.get('credit_enhancement', 0.08),
            last_row.get('subordination_level', 0.05),
            period_ahead  # months_since_origination increases with prediction period
        ]

        return features

    def _format_predictions(self, historical_data, predictions, periods_ahead):
        """
        Format predictions into a DataFrame with dates

        Args:
            historical_data: Historical data with dates
            predictions: List of prediction dictionaries
            periods_ahead: Number of periods predicted

        Returns:
            DataFrame with formatted predictions
        """
        # Determine the date range for predictions
        if 'date' in historical_data.columns:
            last_date = pd.to_datetime(historical_data['date'].iloc[-1])
        else:
            last_date = datetime.now()

        # Create date range for predictions (assuming monthly data)
        future_dates = pd.date_range(
            start=last_date + timedelta(days=30),
            periods=periods_ahead,
            freq='MS'
        )

        # Create DataFrame
        pred_df = pd.DataFrame(predictions)
        pred_df['date'] = future_dates
        pred_df['is_prediction'] = True

        logger.info(f"Generated {len(pred_df)} predictions")
        return pred_df


def generate_sample_historical_data(n_periods=36):
    """
    Generate sample historical delinquency data for demonstration

    Args:
        n_periods: Number of historical periods to generate

    Returns:
        DataFrame with historical delinquency data
    """
    logger.info(f"Generating {n_periods} periods of sample historical data")

    # Generate dates (monthly)
    end_date = datetime.now()
    dates = pd.date_range(
        end=end_date,
        periods=n_periods,
        freq='MS'
    )

    # Generate synthetic delinquency data with trends
    np.random.seed(42)

    # Create base patterns with seasonal variation
    time_points = np.arange(n_periods)
    seasonal = 0.005 * np.sin(2 * np.pi * time_points / 12)

    # 30-day delinquencies (most common)
    delinq_30 = 0.025 + seasonal + np.random.normal(0, 0.003, n_periods)
    delinq_30 = np.clip(delinq_30, 0.01, 0.05)

    # 60-day delinquencies (less common)
    delinq_60 = 0.015 + seasonal * 0.7 + np.random.normal(0, 0.002, n_periods)
    delinq_60 = np.clip(delinq_60, 0.005, 0.03)

    # 90+ day delinquencies (least common)
    delinq_90 = 0.008 + seasonal * 0.5 + np.random.normal(0, 0.001, n_periods)
    delinq_90 = np.clip(delinq_90, 0.002, 0.02)

    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'delinquency_30_days': delinq_30,
        'delinquency_60_days': delinq_60,
        'delinquency_90_plus_days': delinq_90,
        'is_prediction': False
    })

    logger.info(f"Generated historical data with date range: {dates[0]} to {dates[-1]}")
    return df
