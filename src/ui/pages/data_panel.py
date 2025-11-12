"""
Data Panel - Filter and view SEC ABS filing data
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px


def render(data_loader, filters):
    """
    Render the Data panel with filters and data display

    Args:
        data_loader: ABSDataLoader instance
        filters: Dictionary of current filters
    """
    st.markdown("## 📋 Data Explorer")
    st.markdown("Filter and explore SEC ABS filing data with comprehensive search options.")

    # Create filter section
    st.markdown("### 🔍 Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Date range filter
        st.markdown("**Date Range**")
        date_preset = st.selectbox(
            "Quick Select",
            ["Last 30 Days", "Last 90 Days", "Last 6 Months", "Last Year", "Custom"],
            index=1
        )

        if date_preset == "Last 30 Days":
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
        elif date_preset == "Last 90 Days":
            start_date = datetime.now() - timedelta(days=90)
            end_date = datetime.now()
        elif date_preset == "Last 6 Months":
            start_date = datetime.now() - timedelta(days=180)
            end_date = datetime.now()
        elif date_preset == "Last Year":
            start_date = datetime.now() - timedelta(days=365)
            end_date = datetime.now()
        else:  # Custom
            start_date = st.date_input(
                "Start Date",
                value=filters['start_date'],
                max_value=datetime.now()
            )
            end_date = st.date_input(
                "End Date",
                value=filters['end_date'],
                max_value=datetime.now()
            )

        filters['start_date'] = start_date
        filters['end_date'] = end_date

    with col2:
        # Asset Class filter
        st.markdown("**Asset Class**")
        asset_classes = data_loader.get_asset_classes()
        asset_class_options = ["All"] + asset_classes
        selected_asset_class = st.selectbox(
            "Select Asset Class",
            asset_class_options,
            index=0
        )
        filters['asset_class'] = selected_asset_class

        # Form Type filter
        st.markdown("**Form Type**")
        form_types = data_loader.get_form_types()
        selected_form_types = st.multiselect(
            "Select Form Types",
            form_types,
            default=None,
            placeholder="All form types"
        )
        filters['form_type'] = selected_form_types if selected_form_types else None

    with col3:
        # Company filter
        st.markdown("**Company**")
        companies = data_loader.get_unique_companies()

        if companies:
            company_options = [f"{c['company_name']} ({c['cik']})" for c in companies]
            selected_companies = st.multiselect(
                "Select Companies",
                company_options,
                default=None,
                placeholder="All companies"
            )

            if selected_companies:
                # Extract CIKs from selections
                ciks = [comp.split("(")[-1].strip(")") for comp in selected_companies]
                filters['company'] = ciks
            else:
                filters['company'] = None
        else:
            st.info("No companies available")
            filters['company'] = None

    # Apply filters button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Apply Filters", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("🗑️ Reset Filters", use_container_width=True):
            filters['asset_class'] = 'All'
            filters['form_type'] = None
            filters['company'] = None
            st.rerun()

    st.markdown("---")

    # Load data with filters
    with st.spinner("Loading data..."):
        df = data_loader.get_filings(
            start_date=filters['start_date'].strftime('%Y-%m-%d') if isinstance(filters['start_date'], datetime) else str(filters['start_date']),
            end_date=filters['end_date'].strftime('%Y-%m-%d') if isinstance(filters['end_date'], datetime) else str(filters['end_date']),
            asset_class=filters['asset_class'] if filters['asset_class'] != "All" else None,
            form_types=filters['form_type'],  # Now accepts list
            ciks=filters['company']  # Now accepts list
        )

    # Display summary metrics
    if not df.empty:
        st.markdown("### 📊 Data Summary")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Filings", f"{len(df):,}")

        with col2:
            unique_companies = df['company_name'].nunique()
            st.metric("Companies", f"{unique_companies:,}")

        with col3:
            unique_asset_classes = df['asset_class'].nunique()
            st.metric("Asset Classes", f"{unique_asset_classes}")

        with col4:
            if 'current_pool_balance' in df.columns:
                total_balance = df['current_pool_balance'].sum()
                st.metric("Total Pool Balance", f"${total_balance/1e9:.2f}B")
            else:
                st.metric("Total Pool Balance", "N/A")

        with col5:
            if 'delinquency_90_plus_days' in df.columns:
                avg_delinq = df['delinquency_90_plus_days'].mean() * 100
                st.metric("Avg 90+ Day Delinq", f"{avg_delinq:.2f}%")
            else:
                st.metric("Avg 90+ Day Delinq", "N/A")

        st.markdown("---")

        # Data distribution visualizations
        st.markdown("### 📈 Data Distribution")

        col1, col2 = st.columns(2)

        with col1:
            # Filings by Asset Class
            if 'asset_class' in df.columns:
                asset_class_counts = df['asset_class'].value_counts()
                fig = px.pie(
                    values=asset_class_counts.values,
                    names=asset_class_counts.index,
                    title="Filings by Asset Class",
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Filings by Form Type
            if 'form_type' in df.columns:
                form_type_counts = df['form_type'].value_counts()
                fig = px.bar(
                    x=form_type_counts.index,
                    y=form_type_counts.values,
                    title="Filings by Form Type",
                    labels={'x': 'Form Type', 'y': 'Count'}
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # Filings over time
        if 'filing_date' in df.columns:
            df_time = df.copy()
            df_time['filing_date'] = pd.to_datetime(df_time['filing_date'])
            df_time = df_time.sort_values('filing_date')

            # Group by date and count
            filings_by_date = df_time.groupby(df_time['filing_date'].dt.date).size().reset_index()
            filings_by_date.columns = ['Date', 'Count']

            fig = px.line(
                filings_by_date,
                x='Date',
                y='Count',
                title="Filings Over Time",
                labels={'Count': 'Number of Filings'}
            )
            fig.update_traces(line_color='#1f77b4', line_width=2)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Data table
        st.markdown("### 📄 Filing Details")

        # Select columns to display
        display_columns = [
            'filing_date', 'company_name', 'form_type', 'asset_class',
            'current_pool_balance', 'delinquency_90_plus_days',
            'cumulative_default_rate', 'weighted_average_fico'
        ]

        # Filter to existing columns
        display_columns = [col for col in display_columns if col in df.columns]

        # Format the dataframe
        df_display = df[display_columns].copy()

        # Format numeric columns
        if 'current_pool_balance' in df_display.columns:
            df_display['current_pool_balance'] = df_display['current_pool_balance'].apply(
                lambda x: f"${x/1e6:.2f}M" if pd.notnull(x) else "N/A"
            )
        if 'delinquency_90_plus_days' in df_display.columns:
            df_display['delinquency_90_plus_days'] = df_display['delinquency_90_plus_days'].apply(
                lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "N/A"
            )
        if 'cumulative_default_rate' in df_display.columns:
            df_display['cumulative_default_rate'] = df_display['cumulative_default_rate'].apply(
                lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "N/A"
            )

        # Rename columns for display
        df_display.columns = [col.replace('_', ' ').title() for col in df_display.columns]

        # Display with pagination
        st.dataframe(
            df_display,
            use_container_width=True,
            height=400,
            hide_index=True
        )

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Dataset (CSV)",
            data=csv,
            file_name=f"abs_filings_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=False
        )

    else:
        st.warning("No data found matching the selected filters. Try adjusting your filter criteria.")
        st.info("💡 Tip: Select 'All' for Asset Class and Form Type to see all available data.")
