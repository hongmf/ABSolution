"""
Data loader utilities for dashboard
Loads data from DynamoDB or generates sample data for testing
"""

import pandas as pd
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import numpy as np

logger = logging.getLogger(__name__)


def load_data_from_dynamodb(region: str = 'us-east-1',
                            environment: str = 'dev') -> Dict[str, pd.DataFrame]:
    """
    Load data from DynamoDB tables

    Args:
        region: AWS region
        environment: Environment (dev, prod)

    Returns:
        Dictionary of DataFrames with different data types
    """
    logger.info(f"Loading data from DynamoDB in {region} ({environment} environment)")

    dynamodb = boto3.resource('dynamodb', region_name=region)

    data = {}

    try:
        # Load risk scores
        risk_scores_table = dynamodb.Table(f'abs-risk-scores-{environment}')
        risk_response = risk_scores_table.scan()
        if risk_response.get('Items'):
            data['risk_scores'] = pd.DataFrame(risk_response['Items'])
            # Convert filing_date to datetime
            if 'filing_date' in data['risk_scores'].columns:
                data['risk_scores']['filing_date'] = pd.to_datetime(
                    data['risk_scores']['filing_date']
                )
            logger.info(f"Loaded {len(data['risk_scores'])} risk scores")

        # Load filings for delinquency data
        filings_table = dynamodb.Table(f'abs-filings-{environment}')
        filings_response = filings_table.scan()
        if filings_response.get('Items'):
            filings_df = pd.DataFrame(filings_response['Items'])

            # Convert dates
            if 'filing_date' in filings_df.columns:
                filings_df['filing_date'] = pd.to_datetime(filings_df['filing_date'])

            # Extract delinquency data
            if 'delinquency_rate' in filings_df.columns:
                data['delinquencies'] = filings_df[['filing_date', 'delinquency_rate']].copy()
                data['delinquencies'] = data['delinquencies'].sort_values('filing_date')
                logger.info(f"Loaded {len(data['delinquencies'])} delinquency records")

            # Extract issuer data
            if 'issuer_name' in filings_df.columns and 'risk_score' in filings_df.columns:
                data['issuers'] = filings_df[[
                    'issuer_name', 'filing_date', 'risk_score', 'delinquency_rate',
                    'fico_score', 'pool_balance'
                ]].copy() if all(col in filings_df.columns for col in
                               ['issuer_name', 'filing_date', 'risk_score', 'delinquency_rate',
                                'fico_score', 'pool_balance']) else filings_df[
                    ['issuer_name', 'filing_date', 'risk_score']
                ].copy()
                logger.info(f"Loaded {len(data['issuers'])} issuer records")

            # Calculate asset class metrics
            if 'asset_class' in filings_df.columns:
                asset_class_data = filings_df.groupby('asset_class').agg({
                    'risk_score': 'mean',
                    'delinquency_rate': 'mean'
                }).reset_index()
                asset_class_data.columns = ['asset_class', 'avg_risk_score', 'avg_delinquency_rate']
                data['asset_classes'] = asset_class_data
                logger.info(f"Calculated metrics for {len(data['asset_classes'])} asset classes")

    except Exception as e:
        logger.error(f"Error loading data from DynamoDB: {e}")
        logger.warning("Falling back to sample data")
        return generate_sample_data()

    # If no data was loaded, generate sample data
    if not data:
        logger.warning("No data found in DynamoDB, generating sample data")
        return generate_sample_data()

    return data


def generate_sample_data(n_records: int = 1000, n_issuers: int = 20) -> Dict[str, pd.DataFrame]:
    """
    Generate sample data for testing and demonstration

    Args:
        n_records: Number of records to generate
        n_issuers: Number of unique issuers

    Returns:
        Dictionary of DataFrames with sample data
    """
    logger.info(f"Generating {n_records} sample records for {n_issuers} issuers")

    np.random.seed(42)

    # Generate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, periods=n_records)

    # Asset classes
    asset_classes = ['Auto', 'Credit Card', 'Student Loan', 'Equipment', 'Mortgage']

    # Issuer names
    issuer_names = [f'Issuer {chr(65 + i)}' for i in range(n_issuers)]

    # Generate risk scores
    risk_scores_df = pd.DataFrame({
        'filing_date': dates,
        'risk_score': np.random.beta(2, 5, n_records),  # Skewed towards lower risk
        'filing_id': [f'filing_{i:06d}' for i in range(n_records)],
        'asset_class': np.random.choice(asset_classes, n_records),
        'issuer_name': np.random.choice(issuer_names, n_records)
    })

    # Generate delinquency data
    delinquency_base = 0.05  # 5% base delinquency
    delinquency_trend = np.linspace(0, 0.03, n_records)  # Increasing trend
    delinquency_noise = np.random.normal(0, 0.01, n_records)
    delinquency_seasonal = 0.02 * np.sin(np.linspace(0, 4 * np.pi, n_records))  # Seasonal pattern

    delinquencies_df = pd.DataFrame({
        'filing_date': dates,
        'delinquency_rate': np.clip(
            delinquency_base + delinquency_trend + delinquency_noise + delinquency_seasonal,
            0, 0.3
        )
    })

    # Generate issuer-specific data
    issuers_data = []
    for issuer in issuer_names:
        n_issuer_records = n_records // n_issuers
        issuer_dates = pd.date_range(start=start_date, end=end_date, periods=n_issuer_records)

        # Each issuer has a base risk level with some drift
        base_risk = np.random.uniform(0.2, 0.7)
        risk_drift = np.random.uniform(-0.1, 0.1, n_issuer_records).cumsum() * 0.01

        # Generate FICO scores (higher FICO = lower risk)
        fico_base = 700 + (1 - base_risk) * 150  # Higher risk issuers have lower FICO
        fico_scores = np.random.normal(fico_base, 50, n_issuer_records).clip(300, 850)

        # Pool balance decreases over time
        initial_balance = np.random.uniform(1e7, 1e9)
        pool_balances = initial_balance * np.exp(-np.linspace(0, 0.5, n_issuer_records))

        issuer_df = pd.DataFrame({
            'issuer_name': issuer,
            'filing_date': issuer_dates,
            'risk_score': np.clip(base_risk + risk_drift + np.random.normal(0, 0.05, n_issuer_records), 0, 1),
            'delinquency_rate': np.random.beta(2, 10, n_issuer_records),
            'fico_score': fico_scores,
            'pool_balance': pool_balances
        })
        issuers_data.append(issuer_df)

    issuers_df = pd.concat(issuers_data, ignore_index=True)

    # Calculate asset class metrics
    asset_class_metrics = []
    for asset_class in asset_classes:
        # Different asset classes have different risk profiles
        risk_profiles = {
            'Auto': (0.3, 0.08),  # medium risk, medium delinquency
            'Credit Card': (0.5, 0.12),  # higher risk, higher delinquency
            'Student Loan': (0.35, 0.10),  # medium-high risk
            'Equipment': (0.25, 0.06),  # lower risk
            'Mortgage': (0.20, 0.05)  # lowest risk
        }
        avg_risk, avg_delinq = risk_profiles.get(asset_class, (0.3, 0.08))

        asset_class_metrics.append({
            'asset_class': asset_class,
            'avg_risk_score': avg_risk + np.random.normal(0, 0.05),
            'avg_delinquency_rate': avg_delinq + np.random.normal(0, 0.02)
        })

    asset_classes_df = pd.DataFrame(asset_class_metrics)

    logger.info("Sample data generation complete")

    return {
        'risk_scores': risk_scores_df,
        'delinquencies': delinquencies_df,
        'issuers': issuers_df,
        'asset_classes': asset_classes_df
    }


def export_sample_data_to_csv(output_dir: str = './sample_data'):
    """
    Export generated sample data to CSV files

    Args:
        output_dir: Directory to save CSV files
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    data = generate_sample_data()

    for name, df in data.items():
        filepath = os.path.join(output_dir, f'{name}.csv')
        df.to_csv(filepath, index=False)
        logger.info(f"Exported {name} to {filepath}")


if __name__ == '__main__':
    # Test data generation
    logging.basicConfig(level=logging.INFO)
    data = generate_sample_data()

    print("\nGenerated Sample Data Summary:")
    print("=" * 50)
    for name, df in data.items():
        print(f"\n{name}:")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Sample:\n{df.head(3)}")
