"""
ABSolution: AWS-Native ABS Analytics Platform
Streamlit dashboard for analyzing Asset-Backed Securities
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path
import numpy as np
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data.abs_data_loader import ABSDataLoader
from ui.pages import sec_explorer_panel, prediction_panel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="ABSolution Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 4.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        letter-spacing: -2px;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    /* Add sparkle effect */
    @keyframes sparkle {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .main-header::before {
        content: '✨';
        margin-right: 10px;
        animation: sparkle 2s infinite;
    }
    .main-header::after {
        content: '✨';
        margin-left: 10px;
        animation: sparkle 2s infinite;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_data_loader(use_mock: bool):
    """Initialize the data loader (cached)"""
    return ABSDataLoader(use_mock_data=use_mock)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_all_data(_loader):
    """Load all data from the data loader"""
    return {
        'filings': _loader.load_filings_data(),
        'issuers': _loader.load_issuer_data(),
        'performance': _loader.load_pool_performance(),
        'risk_scores': _loader.load_risk_scores()
    }


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


def predict_local(historical_data, periods_ahead):
    """
    Generate predictions using a simple time-series forecasting model
    Uses Exponential Smoothing with Linear Trend
    """
    logger.info("Using local prediction model (Exponential Smoothing)")

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


def main():
    # Initialize session state
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = ABSDataLoader(use_mock_data=True)

    # Header
    st.markdown('<h1 class="main-header">ABSolution</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AWS-Native ABS Analytics Platform | Real-time insights into Asset-Backed Securities</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Data source selection
        use_mock_data = st.checkbox(
            "Use Mock Data",
            value=True,
            help="Toggle between mock data (for demo) and AWS data sources"
        )

        if st.button("Refresh Data"):
            st.cache_data.clear()
            st.session_state.data_loader = ABSDataLoader(use_mock_data=use_mock_data)
            st.success("Data refreshed!")

        st.divider()

        st.header("📊 Filters")

        # Load data
        data = load_all_data(st.session_state.data_loader)

        # Asset class filter
        asset_classes = ['All'] + sorted(data['filings']['asset_class'].unique().tolist())
        selected_asset_class = st.selectbox("Asset Class", asset_classes)

        # Issuer filter
        issuers = sorted(data['filings']['issuer_name'].unique().tolist())
        selected_issuers = st.multiselect(
            "Issuers",
            issuers,
            default=issuers,
            help="Select one or more issuers to analyze"
        )

        # Date range filter
        min_date = data['filings']['filing_date'].min().date()
        max_date = data['filings']['filing_date'].max().date()

        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    # Apply filters
    filtered_filings = data['filings'].copy()

    if selected_asset_class != 'All':
        filtered_filings = filtered_filings[filtered_filings['asset_class'] == selected_asset_class]

    if selected_issuers:
        filtered_filings = filtered_filings[filtered_filings['issuer_name'].isin(selected_issuers)]

    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_filings = filtered_filings[
            (filtered_filings['filing_date'].dt.date >= start_date) &
            (filtered_filings['filing_date'].dt.date <= end_date)
        ]

    # Main dashboard
    # KPI Metrics
    st.header("📈 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_filings = len(filtered_filings)
        st.metric("Total Filings", f"{total_filings:,}")

    with col2:
        total_balance = filtered_filings['current_balance'].sum()
        st.metric("Total Current Balance", f"${total_balance/1e9:.2f}B")

    with col3:
        avg_fico = filtered_filings['average_fico'].mean()
        st.metric("Average FICO Score", f"{avg_fico:.0f}")

    with col4:
        avg_delinquency = filtered_filings['delinquency_rate'].mean() * 100
        st.metric("Avg Delinquency Rate", f"{avg_delinquency:.2f}%")

    st.divider()

    # Charts
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📊 Overview", "🏢 Issuers", "⚠️ Risk Analysis", "📋 Raw Data", "📈 Plot", "🔍 SEC Explorer", "🔮 Prediction"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Filings by Asset Class")
            asset_class_counts = filtered_filings['asset_class'].value_counts()
            fig = px.pie(
                values=asset_class_counts.values,
                names=asset_class_counts.index,
                title="Distribution of Asset Classes"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Current Balance by Asset Class")
            balance_by_class = filtered_filings.groupby('asset_class')['current_balance'].sum()
            fig = px.bar(
                x=balance_by_class.index,
                y=balance_by_class.values / 1e9,
                labels={'x': 'Asset Class', 'y': 'Current Balance ($B)'},
                title="Total Balance by Asset Class"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Delinquency Rate Trends")
        # Group by date and calculate average delinquency
        trend_data = filtered_filings.groupby(filtered_filings['filing_date'].dt.to_period('M'))['delinquency_rate'].mean()
        trend_data.index = trend_data.index.to_timestamp()

        fig = px.line(
            x=trend_data.index,
            y=trend_data.values * 100,
            labels={'x': 'Date', 'y': 'Delinquency Rate (%)'},
            title="Average Delinquency Rate Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Issuer Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top Issuers by Filing Count")
            issuer_counts = filtered_filings['issuer_name'].value_counts().head(10)
            fig = px.bar(
                x=issuer_counts.values,
                y=issuer_counts.index,
                orientation='h',
                labels={'x': 'Number of Filings', 'y': 'Issuer'},
                title="Top 10 Issuers"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("FICO Score Distribution")
            fig = px.histogram(
                filtered_filings,
                x='average_fico',
                nbins=30,
                labels={'average_fico': 'Average FICO Score'},
                title="Distribution of FICO Scores"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Issuer comparison table
        st.subheader("Issuer Comparison")
        issuer_summary = filtered_filings.groupby('issuer_name').agg({
            'accession_number': 'count',
            'current_balance': 'sum',
            'delinquency_rate': 'mean',
            'average_fico': 'mean'
        }).round(2)
        issuer_summary.columns = ['Total Filings', 'Total Balance', 'Avg Delinquency', 'Avg FICO']
        issuer_summary['Total Balance'] = issuer_summary['Total Balance'].apply(lambda x: f"${x/1e9:.2f}B")
        issuer_summary['Avg Delinquency'] = issuer_summary['Avg Delinquency'].apply(lambda x: f"{x*100:.2f}%")

        st.dataframe(issuer_summary, use_container_width=True)

    with tab3:
        st.subheader("Risk Analysis")

        risk_scores_df = data['risk_scores']

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Risk Category Distribution")
            risk_counts = risk_scores_df['risk_category'].value_counts()
            fig = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                title="Risk Categories",
                color=risk_counts.index,
                color_discrete_map={'Low': 'green', 'Medium': 'orange', 'High': 'red'}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Risk Score Distribution")
            fig = px.histogram(
                risk_scores_df,
                x='risk_score',
                nbins=20,
                labels={'risk_score': 'Risk Score'},
                title="Distribution of Risk Scores"
            )
            st.plotly_chart(fig, use_container_width=True)

        # High risk deals
        st.subheader("⚠️ High Risk Deals")
        high_risk = risk_scores_df[risk_scores_df['risk_category'] == 'High'].sort_values('risk_score', ascending=False)

        if len(high_risk) > 0:
            display_cols = ['deal_name', 'risk_score', 'delinquency_forecast', 'confidence_level', 'alert_triggered']
            st.dataframe(
                high_risk[display_cols].head(10),
                use_container_width=True,
                column_config={
                    "risk_score": st.column_config.ProgressColumn(
                        "Risk Score",
                        format="%.2f",
                        min_value=0,
                        max_value=1,
                    ),
                    "delinquency_forecast": st.column_config.NumberColumn(
                        "Delinquency Forecast",
                        format="%.2f%%",
                    ),
                    "confidence_level": st.column_config.ProgressColumn(
                        "Confidence",
                        format="%.0f%%",
                        min_value=0,
                        max_value=1,
                    ),
                    "alert_triggered": st.column_config.CheckboxColumn(
                        "Alert",
                    )
                }
            )
        else:
            st.info("No high-risk deals found in the current dataset.")

    with tab4:
        st.subheader("Raw Filings Data")

        # Display options
        col1, col2 = st.columns([3, 1])
        with col2:
            rows_to_show = st.number_input("Rows to display", min_value=10, max_value=1000, value=50, step=10)

        # Display dataframe
        st.dataframe(
            filtered_filings.head(rows_to_show),
            use_container_width=True,
            column_config={
                "filing_date": st.column_config.DateColumn("Filing Date", format="YYYY-MM-DD"),
                "current_balance": st.column_config.NumberColumn("Current Balance", format="$%.2f"),
                "original_balance": st.column_config.NumberColumn("Original Balance", format="$%.2f"),
                "delinquency_rate": st.column_config.ProgressColumn(
                    "Delinquency Rate",
                    format="%.2f%%",
                    min_value=0,
                    max_value=0.2,
                ),
            }
        )

        # Download button
        csv = filtered_filings.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=f"abs_filings_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    with tab5:
        st.subheader("📈 Data Visualization")
        
        if len(filtered_filings) > 0:
            # Show data overview first
            st.write(f"**Dataset Size:** {filtered_filings.shape[0]} rows × {filtered_filings.shape[1]} columns")
            st.write("**First 5 rows:**")
            st.dataframe(filtered_filings.head())
            
            # Generate multiple plots automatically
            st.subheader("📊 Generated Visualizations")
            
            import matplotlib.pyplot as plt
            import seaborn as sns
            import matplotlib
            matplotlib.use('Agg')
            
            # Create 2x2 grid of plots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # Plot 1: Delinquency Rate Distribution
            if 'delinquency_rate' in filtered_filings.columns:
                filtered_filings['delinquency_rate'].hist(bins=20, ax=ax1, color='skyblue', alpha=0.7)
                ax1.set_title('Delinquency Rate Distribution')
                ax1.set_xlabel('Delinquency Rate')
                ax1.set_ylabel('Frequency')
                ax1.grid(True, alpha=0.3)
            
            # Plot 2: Asset Class Distribution
            if 'asset_class' in filtered_filings.columns:
                filtered_filings['asset_class'].value_counts().plot(kind='bar', ax=ax2, color='lightcoral')
                ax2.set_title('Asset Class Distribution')
                ax2.set_xlabel('Asset Class')
                ax2.set_ylabel('Count')
                ax2.tick_params(axis='x', rotation=45)
                ax2.grid(True, alpha=0.3)
            
            # Plot 3: Current Balance Distribution
            if 'current_balance' in filtered_filings.columns:
                (filtered_filings['current_balance'] / 1e9).hist(bins=20, ax=ax3, color='lightgreen', alpha=0.7)
                ax3.set_title('Current Balance Distribution')
                ax3.set_xlabel('Current Balance ($B)')
                ax3.set_ylabel('Frequency')
                ax3.grid(True, alpha=0.3)
            
            # Plot 4: FICO vs Delinquency Scatter
            if 'average_fico' in filtered_filings.columns and 'delinquency_rate' in filtered_filings.columns:
                ax4.scatter(filtered_filings['average_fico'], filtered_filings['delinquency_rate'], alpha=0.6, color='purple')
                ax4.set_title('FICO Score vs Delinquency Rate')
                ax4.set_xlabel('Average FICO Score')
                ax4.set_ylabel('Delinquency Rate')
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Additional relationship analysis
            if len(filtered_filings.select_dtypes(include=['number']).columns) >= 2:
                st.subheader("📈 Relationship Analysis")
                fig3, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(16, 6))
                
                # Balance vs FICO scatter
                if 'current_balance' in filtered_filings.columns and 'average_fico' in filtered_filings.columns:
                    ax_left.scatter(filtered_filings['current_balance'] / 1e9, filtered_filings['average_fico'], alpha=0.6, color='green')
                    ax_left.set_title('Current Balance vs FICO Score')
                    ax_left.set_xlabel('Current Balance ($B)')
                    ax_left.set_ylabel('Average FICO Score')
                    ax_left.grid(True, alpha=0.3)
                
                # Original vs Current Balance
                if 'original_balance' in filtered_filings.columns and 'current_balance' in filtered_filings.columns:
                    ax_right.scatter(filtered_filings['original_balance'] / 1e9, filtered_filings['current_balance'] / 1e9, alpha=0.6, color='red')
                    ax_right.set_title('Original vs Current Balance')
                    ax_right.set_xlabel('Original Balance ($B)')
                    ax_right.set_ylabel('Current Balance ($B)')
                    ax_right.grid(True, alpha=0.3)
                
                plt.tight_layout()
                st.pyplot(fig3)
            
            # Correlation heatmap
            numeric_cols = filtered_filings.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 1:
                st.subheader("📈 Correlation Matrix")
                fig2, ax = plt.subplots(figsize=(12, 8))
                correlation_matrix = filtered_filings[numeric_cols].corr()
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', ax=ax, fmt='.2f')
                ax.set_title('Correlation Matrix')
                st.pyplot(fig2)
                
        else:
            st.info("No data available for plotting. Please adjust your filters.")

    with tab6:
        # SEC Data Explorer Panel
        sec_explorer_panel.render()

    with tab7:
        # Prediction Panel
        prediction_panel.render()

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>ABSolution Analytics Platform | Powered by AWS Services</p>
        <p>Data Source: {} | Last Updated: {}</p>
    </div>
    """.format(
        "Mock Data (Demo Mode)" if use_mock_data else "AWS (S3, Athena, SageMaker)",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
