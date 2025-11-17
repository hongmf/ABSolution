"""
Prediction Panel - ML-based delinquency rate predictions
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def predict_exponential_smoothing(historical_data, periods_ahead):
    """
    Generate predictions using Exponential Smoothing with Linear Trend
    """
    logger.info("Using Exponential Smoothing model")

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

        predictions.append(pred)

    return format_predictions(historical_data, predictions, periods_ahead)


def predict_malp(historical_data, periods_ahead):
    """
    Generate predictions using MALP (Moving Average Linear Prediction)
    Uses weighted moving averages with polynomial trend fitting
    """
    logger.info("Using MALP (Moving Average Linear Prediction) model")

    # Use more historical data for better trend estimation
    window_size = min(24, len(historical_data))  # Last 24 periods or all available
    recent_data = historical_data.tail(window_size)

    # Calculate trends for each delinquency category
    categories = ['30_days', '60_days', '90_plus_days']
    predictions = []

    for i in range(1, periods_ahead + 1):
        pred = {'period': i}

        for category in categories:
            col_name = f'delinquency_{category}'
            if col_name in recent_data.columns:
                values = recent_data[col_name].values

                # Apply weighted moving average (more weight to recent values)
                weights = np.exp(np.linspace(-1, 0, len(values)))
                weights = weights / weights.sum()
                weighted_avg = np.average(values, weights=weights)

                # Fit polynomial trend (degree 2 for slight curvature)
                x = np.arange(len(values))
                coeffs = np.polyfit(x, values, deg=2)

                # Predict using polynomial extrapolation
                future_x = len(values) + i - 1
                poly_prediction = np.polyval(coeffs, future_x)

                # Combine weighted average with polynomial prediction
                # Give more weight to polynomial for longer horizons
                blend_factor = min(i / periods_ahead, 0.7)
                predicted_value = (1 - blend_factor) * weighted_avg + blend_factor * poly_prediction

                # Add slight dampening for stability
                dampening = 1 - (0.02 * i)  # 2% dampening per period
                predicted_value = predicted_value * dampening

                # Ensure values stay in reasonable range (0-1 for rates)
                predicted_value = max(0, min(1, predicted_value))

                pred[col_name] = predicted_value
            else:
                pred[col_name] = 0.02  # Default value

        predictions.append(pred)

    return format_predictions(historical_data, predictions, periods_ahead)


def format_predictions(historical_data, predictions, periods_ahead):
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


def create_delinquencies_figure(historical_data, predictions, show_confidence=True, model_name=""):
    """
    Create delinquencies chart figure

    Args:
        historical_data: DataFrame with historical data
        predictions: DataFrame with predictions
        show_confidence: Whether to show confidence intervals
        model_name: Name of the model for the title

    Returns:
        Plotly figure object
    """
    combined_data = pd.concat([historical_data, predictions], ignore_index=True)

    fig = go.Figure()

    if combined_data.empty:
        logger.error("No data available for chart")
        return fig

    colors = {
        '30_days': {
            'historical': '#3498db',
            'prediction': '#5dade2',
            'confidence': 'rgba(93, 173, 226, 0.2)'
        },
        '60_days': {
            'historical': '#f39c12',
            'prediction': '#f8c471',
            'confidence': 'rgba(248, 196, 113, 0.2)'
        },
        '90_plus_days': {
            'historical': '#e74c3c',
            'prediction': '#ec7063',
            'confidence': 'rgba(236, 112, 99, 0.2)'
        }
    }

    categories = [
        ('delinquency_30_days', '30-Day Delinquencies', '30_days'),
        ('delinquency_60_days', '60-Day Delinquencies', '60_days'),
        ('delinquency_90_plus_days', '90+ Day Delinquencies', '90_plus_days')
    ]

    for col_name, display_name, color_key in categories:
        # Add confidence intervals FIRST (so they appear behind the lines)
        prediction_df = combined_data[combined_data['is_prediction']]

        if show_confidence and not prediction_df.empty:
            # Upper confidence bound (transparent fill)
            fig.add_trace(go.Scatter(
                x=prediction_df['date'],
                y=prediction_df[col_name] * 1.15,
                mode='lines',
                name=f'{display_name} Confidence',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))

            # Lower confidence bound (fills to upper bound)
            fig.add_trace(go.Scatter(
                x=prediction_df['date'],
                y=prediction_df[col_name] * 0.85,
                mode='lines',
                name=f'{display_name} Confidence Lower',
                line=dict(width=0),
                fill='tonexty',
                fillcolor=colors[color_key]['confidence'],
                showlegend=False,
                hoverinfo='skip'
            ))

        # Historical data (solid lines) - drawn AFTER confidence intervals
        historical_df = combined_data[~combined_data['is_prediction']]
        if not historical_df.empty:
            fig.add_trace(go.Scatter(
                x=historical_df['date'],
                y=historical_df[col_name],
                mode='lines+markers',
                name=f'{display_name} (Historical)',
                line=dict(color=colors[color_key]['historical'], width=3),
                marker=dict(size=6),
                hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Rate: %{y:.2%}<extra></extra>'
            ))

        # Predicted data (dashed lines) - drawn ON TOP of confidence intervals
        if not prediction_df.empty:
            fig.add_trace(go.Scatter(
                x=prediction_df['date'],
                y=prediction_df[col_name],
                mode='lines+markers',
                name=f'{display_name} (Predicted)',
                line=dict(color=colors[color_key]['prediction'], width=3, dash='dash'),
                marker=dict(size=6, symbol='diamond'),
                hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Predicted Rate: %{y:.2%}<extra></extra>'
            ))

    # Add vertical line to separate historical from predictions
    if not historical_data.empty:
        last_historical_date = historical_data['date'].iloc[-1]
        # Add shape instead of vline to avoid timestamp issues
        fig.add_shape(
            type="line",
            x0=last_historical_date,
            x1=last_historical_date,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="gray", width=2, dash="dash"),
            opacity=0.5
        )
        # Add annotation
        fig.add_annotation(
            x=last_historical_date,
            y=1,
            yref="paper",
            text="Prediction Start",
            showarrow=False,
            yshift=10,
            font=dict(size=10, color="gray")
        )

    # Update layout
    fig.update_layout(
        title={
            'text': f'Delinquency Rates: Historical Data & ML Predictions{" - " + model_name if model_name else ""}',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        xaxis_title='Date',
        yaxis_title='Delinquency Rate (%)',
        yaxis_tickformat='.1%',
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'family': 'Arial, sans-serif'},
        height=600,
        xaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=0.5),
        yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=0.5)
    )

    return fig


def render():
    """
    Render the Prediction panel
    """
    st.markdown("## 🔮 Delinquency Prediction")
    st.markdown("Use machine learning models to predict future delinquency rates based on historical data.")

    st.markdown("---")

    # Configuration Section
    st.markdown("### ⚙️ Prediction Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Historical Data**")
        historical_periods = st.slider(
            "Number of Historical Periods",
            min_value=12,
            max_value=60,
            value=36,
            step=6,
            help="Number of historical months to use for training"
        )

    with col2:
        st.markdown("**Prediction Model**")
        model_choice = st.selectbox(
            "Select Prediction Model",
            ["Exponential Smoothing", "MALP (Moving Average Linear Prediction)"],
            index=1,
            help="Choose the ML model for predictions"
        )

    with col3:
        st.markdown("**Forecast Horizon**")
        prediction_periods = st.slider(
            "Periods to Predict",
            min_value=3,
            max_value=24,
            value=12,
            step=3,
            help="Number of future months to predict"
        )

    # Additional options
    col1, col2 = st.columns(2)

    with col1:
        show_confidence = st.checkbox(
            "Show Confidence Intervals",
            value=True,
            help="Display confidence bands around predictions"
        )

    with col2:
        show_data_table = st.checkbox(
            "Show Prediction Data Table",
            value=False,
            help="Display the raw prediction values in a table"
        )

    st.markdown("---")

    # Generate Predictions Button
    if st.button("🔮 Generate Predictions", type="primary", use_container_width=True):
        with st.spinner("Generating historical data and predictions..."):
            # Generate sample historical data
            historical_data = generate_sample_historical_data(n_periods=historical_periods)

            # Generate predictions based on selected model
            if model_choice == "Exponential Smoothing":
                predictions = predict_exponential_smoothing(historical_data, prediction_periods)
                model_name = "Exponential Smoothing"
            else:  # MALP
                predictions = predict_malp(historical_data, prediction_periods)
                model_name = "MALP"

            # Store in session state
            st.session_state.prediction_historical = historical_data
            st.session_state.prediction_forecast = predictions
            st.session_state.prediction_model = model_name
            st.session_state.show_confidence = show_confidence

            st.success(f"✓ Generated predictions using {model_name} model!")

    # Display Results
    if 'prediction_historical' in st.session_state and 'prediction_forecast' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 Prediction Results")

        historical_data = st.session_state.prediction_historical
        predictions = st.session_state.prediction_forecast
        model_name = st.session_state.prediction_model
        show_conf = st.session_state.show_confidence

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Historical Periods",
                len(historical_data),
                help="Number of historical data points used"
            )

        with col2:
            st.metric(
                "Forecast Periods",
                len(predictions),
                help="Number of future periods predicted"
            )

        with col3:
            avg_30_pred = predictions['delinquency_30_days'].mean()
            st.metric(
                "Avg 30-Day (Predicted)",
                f"{avg_30_pred:.2%}",
                help="Average predicted 30-day delinquency rate"
            )

        with col4:
            avg_90_pred = predictions['delinquency_90_plus_days'].mean()
            st.metric(
                "Avg 90+ Day (Predicted)",
                f"{avg_90_pred:.2%}",
                help="Average predicted 90+ day delinquency rate"
            )

        st.markdown("---")

        # Create and display chart
        st.markdown("#### 📈 Delinquency Rate Forecast")

        fig = create_delinquencies_figure(
            historical_data,
            predictions,
            show_confidence=show_conf,
            model_name=model_name
        )

        st.plotly_chart(fig, use_container_width=True)

        # Data table (if requested)
        if show_data_table:
            st.markdown("---")
            st.markdown("#### 📋 Prediction Data")

            # Format predictions for display
            display_df = predictions[['date', 'delinquency_30_days', 'delinquency_60_days', 'delinquency_90_plus_days']].copy()
            display_df.columns = ['Date', '30-Day Rate', '60-Day Rate', '90+ Day Rate']

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.DateColumn("Date", format="YYYY-MM"),
                    "30-Day Rate": st.column_config.NumberColumn("30-Day Rate", format="%.3f%%"),
                    "60-Day Rate": st.column_config.NumberColumn("60-Day Rate", format="%.3f%%"),
                    "90+ Day Rate": st.column_config.NumberColumn("90+ Day Rate", format="%.3f%%"),
                }
            )

            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Predictions (CSV)",
                data=csv,
                file_name=f"delinquency_predictions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        # Model Information
        with st.expander("ℹ️ Model Information"):
            st.markdown(f"""
            ### {model_name}

            **Model Details:**
            - **Historical Data Used**: {len(historical_data)} months
            - **Forecast Horizon**: {len(predictions)} months
            - **Delinquency Categories**: 30-day, 60-day, 90+ day

            **Model Description:**
            """)

            if model_name == "Exponential Smoothing":
                st.markdown("""
                Exponential Smoothing is a time series forecasting method that applies exponentially decreasing
                weights to past observations. It uses:
                - Linear trend estimation
                - Recent data weighted more heavily
                - Suitable for short to medium-term forecasts
                """)
            else:  # MALP
                st.markdown("""
                MALP (Moving Average Linear Prediction) is an advanced forecasting method that combines:
                - Weighted moving averages (exponentially weighted)
                - Polynomial trend fitting (degree 2)
                - Adaptive blending based on forecast horizon
                - Dampening for long-term stability
                - Better for capturing non-linear trends
                """)

            st.markdown("""
            **Confidence Intervals:**
            - Upper bound: +15% of predicted value
            - Lower bound: -15% of predicted value
            - Represents uncertainty in predictions

            **Note:** This is a demonstration using synthetic data. In production, use actual historical
            delinquency data from your ABS portfolios.
            """)

    else:
        st.info("👆 Configure the parameters above and click 'Generate Predictions' to see forecasts.")
