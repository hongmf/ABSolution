"""
Analytics Panel - Advanced analytics, visualizations, and insights
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def render(data_loader, filters):
    """
    Render the Analytics panel with visualizations and insights

    Args:
        data_loader: ABSDataLoader instance
        filters: Dictionary of current filters
    """
    st.markdown("## 📈 Analytics Dashboard")
    st.markdown("Deep dive into ABS performance metrics, trends, and risk analytics.")

    # Load data with current filters
    with st.spinner("Loading analytics data..."):
        df = data_loader.get_filings(
            start_date=filters['start_date'].strftime('%Y-%m-%d') if isinstance(filters['start_date'], datetime) else str(filters['start_date']),
            end_date=filters['end_date'].strftime('%Y-%m-%d') if isinstance(filters['end_date'], datetime) else str(filters['end_date']),
            asset_class=filters['asset_class'] if filters['asset_class'] != "All" else None,
            form_type=filters['form_type'] if filters['form_type'] != "All" else None,
            cik=filters['company']
        )

        # Load risk scores
        risk_df = data_loader.get_risk_scores(
            cik=filters['company'],
            asset_class=filters['asset_class'] if filters['asset_class'] != "All" else None
        )

    if df.empty:
        st.warning("No data available for analytics. Please adjust your filters in the Data panel.")
        return

    # Analytics Type Selector
    analytics_type = st.radio(
        "Select Analytics View",
        ["Performance Metrics", "Risk Analytics", "Comparative Analysis", "Trend Analysis"],
        horizontal=True
    )

    st.markdown("---")

    if analytics_type == "Performance Metrics":
        render_performance_metrics(df)
    elif analytics_type == "Risk Analytics":
        render_risk_analytics(df, risk_df)
    elif analytics_type == "Comparative Analysis":
        render_comparative_analysis(df)
    elif analytics_type == "Trend Analysis":
        render_trend_analysis(df)


def render_performance_metrics(df):
    """Render performance metrics section"""
    st.markdown("### 🎯 Performance Metrics")

    # Key Performance Indicators
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if 'delinquency_30_days' in df.columns:
            avg_delinq_30 = df['delinquency_30_days'].mean() * 100
            st.metric(
                "Avg 30-Day Delinquency",
                f"{avg_delinq_30:.2f}%",
                delta=None,
                help="Average 30-day delinquency rate across all filings"
            )

    with col2:
        if 'delinquency_60_days' in df.columns:
            avg_delinq_60 = df['delinquency_60_days'].mean() * 100
            st.metric(
                "Avg 60-Day Delinquency",
                f"{avg_delinq_60:.2f}%"
            )

    with col3:
        if 'delinquency_90_plus_days' in df.columns:
            avg_delinq_90 = df['delinquency_90_plus_days'].mean() * 100
            st.metric(
                "Avg 90+ Day Delinquency",
                f"{avg_delinq_90:.2f}%"
            )

    with col4:
        if 'cumulative_default_rate' in df.columns:
            avg_default = df['cumulative_default_rate'].mean() * 100
            st.metric(
                "Avg Default Rate",
                f"{avg_default:.2f}%"
            )

    st.markdown("---")

    # Delinquency Analysis
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Delinquency Cascade")
        if all(col in df.columns for col in ['delinquency_30_days', 'delinquency_60_days', 'delinquency_90_plus_days']):
            delinq_data = {
                '30 Days': df['delinquency_30_days'].mean() * 100,
                '60 Days': df['delinquency_60_days'].mean() * 100,
                '90+ Days': df['delinquency_90_plus_days'].mean() * 100
            }

            fig = go.Figure(data=[
                go.Bar(
                    x=list(delinq_data.keys()),
                    y=list(delinq_data.values()),
                    marker_color=['#ff9999', '#ff6666', '#ff3333'],
                    text=[f"{v:.2f}%" for v in delinq_data.values()],
                    textposition='auto'
                )
            ])
            fig.update_layout(
                title="Average Delinquency by Bucket",
                xaxis_title="Delinquency Bucket",
                yaxis_title="Rate (%)",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Delinquency Distribution")
        if 'delinquency_90_plus_days' in df.columns:
            fig = px.histogram(
                df,
                x='delinquency_90_plus_days',
                nbins=30,
                title="Distribution of 90+ Day Delinquency Rates",
                labels={'delinquency_90_plus_days': 'Delinquency Rate'}
            )
            fig.update_traces(marker_color='#ff6666')
            st.plotly_chart(fig, use_container_width=True)

    # Credit Quality Metrics
    st.markdown("#### 💳 Credit Quality Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        if 'weighted_average_fico' in df.columns:
            avg_fico = df['weighted_average_fico'].mean()
            min_fico = df['weighted_average_fico'].min()
            max_fico = df['weighted_average_fico'].max()

            st.metric("Avg FICO Score", f"{avg_fico:.0f}")
            st.caption(f"Range: {min_fico:.0f} - {max_fico:.0f}")

            # FICO distribution
            fig = px.box(
                df,
                y='weighted_average_fico',
                title="FICO Score Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'weighted_average_ltv' in df.columns:
            avg_ltv = df['weighted_average_ltv'].mean() * 100
            st.metric("Avg LTV Ratio", f"{avg_ltv:.1f}%")

            # LTV distribution
            fig = px.histogram(
                df,
                x='weighted_average_ltv',
                nbins=25,
                title="LTV Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col3:
        if 'weighted_average_dti' in df.columns:
            avg_dti = df['weighted_average_dti'].mean() * 100
            st.metric("Avg DTI Ratio", f"{avg_dti:.1f}%")

            # DTI distribution
            fig = px.histogram(
                df,
                x='weighted_average_dti',
                nbins=25,
                title="DTI Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Pool Balance Analysis
    if 'current_pool_balance' in df.columns:
        st.markdown("---")
        st.markdown("#### 💰 Pool Balance Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # Balance by Asset Class
            if 'asset_class' in df.columns:
                balance_by_asset = df.groupby('asset_class')['current_pool_balance'].sum().sort_values(ascending=False)
                fig = px.bar(
                    x=balance_by_asset.index,
                    y=balance_by_asset.values / 1e9,
                    title="Total Pool Balance by Asset Class",
                    labels={'x': 'Asset Class', 'y': 'Balance ($B)'}
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Top companies by balance
            if 'company_name' in df.columns:
                top_companies = df.groupby('company_name')['current_pool_balance'].sum().sort_values(ascending=False).head(10)
                fig = px.bar(
                    x=top_companies.values / 1e9,
                    y=top_companies.index,
                    orientation='h',
                    title="Top 10 Companies by Pool Balance",
                    labels={'x': 'Balance ($B)', 'y': 'Company'}
                )
                st.plotly_chart(fig, use_container_width=True)


def render_risk_analytics(df, risk_df):
    """Render risk analytics section"""
    st.markdown("### ⚠️ Risk Analytics")

    if risk_df.empty:
        st.info("Risk score data not available. Showing performance-based risk indicators.")

    # Risk Score Distribution
    if not risk_df.empty and 'risk_score' in risk_df.columns:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg_risk = risk_df['risk_score'].mean()
            st.metric("Avg Risk Score", f"{avg_risk:.1f}")

        with col2:
            if 'risk_level' in risk_df.columns:
                high_risk = len(risk_df[risk_df['risk_level'].isin(['HIGH', 'CRITICAL'])])
                st.metric("High Risk Entities", f"{high_risk}")

        with col3:
            if 'delinquency_risk' in risk_df.columns:
                avg_delinq_risk = risk_df['delinquency_risk'].mean()
                st.metric("Avg Delinquency Risk", f"{avg_delinq_risk:.1f}")

        with col4:
            if 'default_risk' in risk_df.columns:
                avg_default_risk = risk_df['default_risk'].mean()
                st.metric("Avg Default Risk", f"{avg_default_risk:.1f}")

        st.markdown("---")

        # Risk Level Distribution
        col1, col2 = st.columns(2)

        with col1:
            if 'risk_level' in risk_df.columns:
                risk_counts = risk_df['risk_level'].value_counts()
                colors = {'LOW': '#00cc00', 'MEDIUM': '#ffcc00', 'HIGH': '#ff9900', 'CRITICAL': '#ff0000'}
                fig = px.pie(
                    values=risk_counts.values,
                    names=risk_counts.index,
                    title="Risk Level Distribution",
                    color=risk_counts.index,
                    color_discrete_map=colors
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Risk Score Distribution
            fig = px.histogram(
                risk_df,
                x='risk_score',
                nbins=30,
                title="Risk Score Distribution",
                labels={'risk_score': 'Risk Score'}
            )
            st.plotly_chart(fig, use_container_width=True)

        # Risk Components
        st.markdown("#### Risk Components Analysis")

        if all(col in risk_df.columns for col in ['delinquency_risk', 'default_risk', 'liquidity_risk']):
            # Calculate average risk components
            risk_components = {
                'Delinquency Risk': risk_df['delinquency_risk'].mean(),
                'Default Risk': risk_df['default_risk'].mean(),
                'Liquidity Risk': risk_df['liquidity_risk'].mean()
            }

            fig = go.Figure(data=[
                go.Bar(
                    x=list(risk_components.keys()),
                    y=list(risk_components.values()),
                    marker_color=['#ff6666', '#ff9966', '#ffcc66'],
                    text=[f"{v:.1f}" for v in risk_components.values()],
                    textposition='auto'
                )
            ])
            fig.update_layout(
                title="Average Risk Component Scores",
                yaxis_title="Score",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        # Risk by Asset Class
        if 'asset_class' in risk_df.columns:
            st.markdown("#### Risk by Asset Class")
            risk_by_asset = risk_df.groupby('asset_class')['risk_score'].agg(['mean', 'min', 'max']).reset_index()

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=risk_by_asset['asset_class'],
                y=risk_by_asset['mean'],
                name='Average',
                error_y=dict(
                    type='data',
                    symmetric=False,
                    array=risk_by_asset['max'] - risk_by_asset['mean'],
                    arrayminus=risk_by_asset['mean'] - risk_by_asset['min']
                )
            ))
            fig.update_layout(
                title="Risk Scores by Asset Class (with Min/Max Range)",
                xaxis_title="Asset Class",
                yaxis_title="Risk Score"
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        # Show performance-based risk indicators
        st.markdown("#### Performance-Based Risk Indicators")

        col1, col2 = st.columns(2)

        with col1:
            # High delinquency rate entities
            if 'delinquency_90_plus_days' in df.columns:
                high_delinq = df[df['delinquency_90_plus_days'] > df['delinquency_90_plus_days'].quantile(0.75)]
                st.metric("High Delinquency Entities", len(high_delinq))

                fig = px.scatter(
                    df,
                    x='weighted_average_fico' if 'weighted_average_fico' in df.columns else df.index,
                    y='delinquency_90_plus_days',
                    color='asset_class' if 'asset_class' in df.columns else None,
                    title="Delinquency vs FICO Score",
                    labels={'delinquency_90_plus_days': '90+ Day Delinquency Rate'}
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # High default rate entities
            if 'cumulative_default_rate' in df.columns:
                high_default = df[df['cumulative_default_rate'] > df['cumulative_default_rate'].quantile(0.75)]
                st.metric("High Default Entities", len(high_default))

                fig = px.box(
                    df,
                    x='asset_class' if 'asset_class' in df.columns else None,
                    y='cumulative_default_rate',
                    title="Default Rate Distribution by Asset Class"
                )
                st.plotly_chart(fig, use_container_width=True)


def render_comparative_analysis(df):
    """Render comparative analysis section"""
    st.markdown("### 📊 Comparative Analysis")

    # Asset Class Comparison
    if 'asset_class' in df.columns:
        st.markdown("#### Compare Asset Classes")

        # Select metrics to compare
        metric_options = []
        if 'delinquency_90_plus_days' in df.columns:
            metric_options.append('delinquency_90_plus_days')
        if 'cumulative_default_rate' in df.columns:
            metric_options.append('cumulative_default_rate')
        if 'weighted_average_fico' in df.columns:
            metric_options.append('weighted_average_fico')
        if 'weighted_average_ltv' in df.columns:
            metric_options.append('weighted_average_ltv')

        if metric_options:
            selected_metric = st.selectbox(
                "Select Metric to Compare",
                metric_options,
                format_func=lambda x: x.replace('_', ' ').title()
            )

            # Create comparison chart
            comparison_data = df.groupby('asset_class')[selected_metric].agg(['mean', 'median', 'std']).reset_index()

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Mean',
                x=comparison_data['asset_class'],
                y=comparison_data['mean'],
                marker_color='#1f77b4'
            ))
            fig.add_trace(go.Bar(
                name='Median',
                x=comparison_data['asset_class'],
                y=comparison_data['median'],
                marker_color='#ff7f0e'
            ))

            fig.update_layout(
                title=f"{selected_metric.replace('_', ' ').title()} by Asset Class",
                xaxis_title="Asset Class",
                yaxis_title=selected_metric.replace('_', ' ').title(),
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Statistical summary table
            st.markdown("#### Statistical Summary")
            summary_df = comparison_data.copy()
            summary_df.columns = ['Asset Class', 'Mean', 'Median', 'Std Dev']
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # Company Comparison
    if 'company_name' in df.columns:
        st.markdown("---")
        st.markdown("#### Company Benchmarking")

        # Top companies by pool balance
        top_companies = df.groupby('company_name').agg({
            'current_pool_balance': 'sum' if 'current_pool_balance' in df.columns else 'count',
            'delinquency_90_plus_days': 'mean' if 'delinquency_90_plus_days' in df.columns else 'count',
            'cumulative_default_rate': 'mean' if 'cumulative_default_rate' in df.columns else 'count',
            'weighted_average_fico': 'mean' if 'weighted_average_fico' in df.columns else 'count'
        }).sort_values('current_pool_balance' if 'current_pool_balance' in df.columns else df.columns[0],
                       ascending=False).head(10)

        # Create heatmap
        fig = px.imshow(
            top_companies.T,
            labels=dict(x="Company", y="Metric", color="Value"),
            title="Top 10 Companies - Key Metrics Heatmap",
            aspect="auto",
            color_continuous_scale="RdYlGn_r"
        )
        st.plotly_chart(fig, use_container_width=True)


def render_trend_analysis(df):
    """Render trend analysis section"""
    st.markdown("### 📉 Trend Analysis")

    if 'filing_date' not in df.columns:
        st.warning("Date information not available for trend analysis.")
        return

    # Convert filing_date to datetime
    df_trend = df.copy()
    df_trend['filing_date'] = pd.to_datetime(df_trend['filing_date'])
    df_trend = df_trend.sort_values('filing_date')

    # Time series aggregation options
    agg_period = st.selectbox(
        "Aggregation Period",
        ["Daily", "Weekly", "Monthly", "Quarterly"],
        index=2
    )

    # Group data by period
    if agg_period == "Daily":
        df_trend['period'] = df_trend['filing_date'].dt.date
    elif agg_period == "Weekly":
        df_trend['period'] = df_trend['filing_date'].dt.to_period('W').dt.start_time
    elif agg_period == "Monthly":
        df_trend['period'] = df_trend['filing_date'].dt.to_period('M').dt.start_time
    else:  # Quarterly
        df_trend['period'] = df_trend['filing_date'].dt.to_period('Q').dt.start_time

    # Metrics to analyze
    st.markdown("#### Performance Metrics Over Time")

    col1, col2 = st.columns(2)

    with col1:
        if 'delinquency_90_plus_days' in df_trend.columns:
            trend_data = df_trend.groupby('period')['delinquency_90_plus_days'].mean().reset_index()
            fig = px.line(
                trend_data,
                x='period',
                y='delinquency_90_plus_days',
                title="90+ Day Delinquency Trend",
                labels={'delinquency_90_plus_days': 'Delinquency Rate', 'period': 'Date'}
            )
            fig.update_traces(line_color='#ff6666', line_width=3)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'cumulative_default_rate' in df_trend.columns:
            trend_data = df_trend.groupby('period')['cumulative_default_rate'].mean().reset_index()
            fig = px.line(
                trend_data,
                x='period',
                y='cumulative_default_rate',
                title="Cumulative Default Rate Trend",
                labels={'cumulative_default_rate': 'Default Rate', 'period': 'Date'}
            )
            fig.update_traces(line_color='#ff9966', line_width=3)
            st.plotly_chart(fig, use_container_width=True)

    # Credit quality trends
    if 'weighted_average_fico' in df_trend.columns:
        st.markdown("#### Credit Quality Trends")
        trend_data = df_trend.groupby('period')['weighted_average_fico'].mean().reset_index()
        fig = px.line(
            trend_data,
            x='period',
            y='weighted_average_fico',
            title="Average FICO Score Trend",
            labels={'weighted_average_fico': 'FICO Score', 'period': 'Date'}
        )
        fig.update_traces(line_color='#00cc00', line_width=3)
        st.plotly_chart(fig, use_container_width=True)

    # Multi-metric comparison
    if all(col in df_trend.columns for col in ['delinquency_90_plus_days', 'cumulative_default_rate']):
        st.markdown("#### Multi-Metric Trend Comparison")

        trend_data = df_trend.groupby('period').agg({
            'delinquency_90_plus_days': 'mean',
            'cumulative_default_rate': 'mean',
            'weighted_average_fico': 'mean' if 'weighted_average_fico' in df_trend.columns else 'count'
        }).reset_index()

        # Normalize metrics for comparison
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()

        metrics_to_plot = ['delinquency_90_plus_days', 'cumulative_default_rate']
        if 'weighted_average_fico' in trend_data.columns:
            metrics_to_plot.append('weighted_average_fico')

        trend_data_normalized = trend_data.copy()
        trend_data_normalized[metrics_to_plot] = scaler.fit_transform(trend_data[metrics_to_plot])

        fig = go.Figure()
        for metric in metrics_to_plot:
            fig.add_trace(go.Scatter(
                x=trend_data_normalized['period'],
                y=trend_data_normalized[metric],
                mode='lines',
                name=metric.replace('_', ' ').title(),
                line=dict(width=2)
            ))

        fig.update_layout(
            title="Normalized Metric Trends (0-1 Scale)",
            xaxis_title="Date",
            yaxis_title="Normalized Value",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Asset class trends
    if 'asset_class' in df_trend.columns and 'delinquency_90_plus_days' in df_trend.columns:
        st.markdown("#### Trends by Asset Class")

        trend_by_asset = df_trend.groupby(['period', 'asset_class'])['delinquency_90_plus_days'].mean().reset_index()

        fig = px.line(
            trend_by_asset,
            x='period',
            y='delinquency_90_plus_days',
            color='asset_class',
            title="Delinquency Trend by Asset Class",
            labels={'delinquency_90_plus_days': 'Delinquency Rate', 'period': 'Date', 'asset_class': 'Asset Class'}
        )
        st.plotly_chart(fig, use_container_width=True)
