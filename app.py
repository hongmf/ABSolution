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

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data.abs_data_loader import ABSDataLoader

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
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
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


def main():
    # Initialize session state
    if 'data_loader' not in st.session_state:
        st.session_state.data_loader = ABSDataLoader(use_mock_data=True)

    # Header
    st.markdown('<h1 class="main-header">ABSolution Analytics Platform</h1>', unsafe_allow_html=True)
    st.markdown("**AWS-Native ABS Analytics** | Real-time insights into Asset-Backed Securities")

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
        issuers = ['All'] + sorted(data['filings']['issuer_name'].unique().tolist())
        selected_issuer = st.selectbox("Issuer", issuers)

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

    if selected_issuer != 'All':
        filtered_filings = filtered_filings[filtered_filings['issuer_name'] == selected_issuer]

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
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏢 Issuers", "⚠️ Risk Analysis", "📋 Raw Data"])

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
