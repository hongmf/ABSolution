"""
SEC Data Explorer Panel - Query and download SEC filings
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
from typing import List, Dict, Optional
import json

# SEC API Configuration
SEC_API_BASE = "https://data.sec.gov"
USER_AGENT = "ABSolution ABS Analytics Platform (contact@example.com)"
REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'data.sec.gov'
}

# Default companies (5 major ABS issuers)
DEFAULT_COMPANIES = [
    {"name": "Ford Motor Credit Company", "cik": "38777"},
    {"name": "GM Financial Company", "cik": "1576940"},
    {"name": "Santander Consumer USA Holdings", "cik": "1548429"},
    {"name": "Capital One Financial Corporation", "cik": "927628"},
    {"name": "American Express Company", "cik": "4962"},
]

# ABS-related form types
ABS_FORM_TYPES = [
    'ABS-EE',    # ABS Informational and Computational Material
    '10-D',      # Asset-Backed Issuer Distribution Report
    '10-K',      # Annual Report
    '8-K',       # Current Report
    'ABS-15G',   # Asset-Backed Securities Report
    '10-Q',      # Quarterly Report
    'S-1',       # Registration Statement
    'S-3',       # Registration Statement
]


def get_company_info(cik: str) -> Dict:
    """
    Get company information from SEC API

    Args:
        cik: Company CIK number

    Returns:
        Dictionary of company information
    """
    # Pad CIK to 10 digits
    cik_padded = cik.zfill(10)
    url = f"{SEC_API_BASE}/submissions/CIK{cik_padded}.json"

    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching company info for CIK {cik}: {str(e)}")
        return {}


def get_company_filings(cik: str, form_types: List[str] = None,
                        start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Get filings for a company from SEC API

    Args:
        cik: Company CIK number
        form_types: List of form types to filter
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        DataFrame of filings
    """
    company_data = get_company_info(cik)

    if not company_data:
        return pd.DataFrame()

    # Extract filing information
    filings = company_data.get('filings', {}).get('recent', {})

    if not filings:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame({
        'accessionNumber': filings.get('accessionNumber', []),
        'filingDate': filings.get('filingDate', []),
        'reportDate': filings.get('reportDate', []),
        'form': filings.get('form', []),
        'fileNumber': filings.get('fileNumber', []),
        'size': filings.get('size', []),
        'primaryDocument': filings.get('primaryDocument', []),
        'primaryDocDescription': filings.get('primaryDocDescription', []),
    })

    if df.empty:
        return df

    # Filter by form type
    if form_types:
        df = df[df['form'].isin(form_types)]

    # Filter by date range
    if start_date:
        df = df[df['filingDate'] >= start_date]
    if end_date:
        df = df[df['filingDate'] <= end_date]

    # Sort by filing date (most recent first)
    df = df.sort_values('filingDate', ascending=False)

    return df


def search_company_by_name(company_name: str) -> List[Dict]:
    """
    Search for companies by name using SEC API
    This is a simplified search - in production, you might want to use
    a more sophisticated company search API

    Args:
        company_name: Company name to search

    Returns:
        List of matching companies
    """
    # Note: SEC doesn't have a direct company search API
    # This is a placeholder - you might want to implement your own search
    # or use the SEC's company tickers JSON file
    st.warning("Company name search is limited. Please use CIK number for accurate results.")
    return []


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_filing_url(cik: str, accession_number: str, primary_document: str) -> str:
    """
    Generate SEC EDGAR URL for a filing

    Args:
        cik: Company CIK
        accession_number: Filing accession number
        primary_document: Primary document filename

    Returns:
        Full URL to the filing
    """
    # Remove dashes from accession number for URL
    accession_no_dashes = accession_number.replace('-', '')
    cik_padded = cik.zfill(10)

    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{primary_document}"


def render():
    """
    Render the SEC Data Explorer panel
    """
    st.markdown("## 🔍 SEC Data Explorer")
    st.markdown("Query and download SEC filings for ABS issuers. Select companies, date ranges, and form types to explore available data.")

    st.markdown("---")

    # Initialize session state
    if 'selected_cik' not in st.session_state:
        st.session_state.selected_cik = None
    if 'company_filings' not in st.session_state:
        st.session_state.company_filings = None
    if 'selected_filings' not in st.session_state:
        st.session_state.selected_filings = []

    # Company Selection Section
    st.markdown("### 🏢 Company Selection")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Radio button for selection method
        selection_method = st.radio(
            "Selection Method",
            ["Select from Default Companies", "Enter Custom CIK"],
            horizontal=True
        )

        if selection_method == "Select from Default Companies":
            # Dropdown of default companies
            company_options = [f"{comp['name']} (CIK: {comp['cik']})" for comp in DEFAULT_COMPANIES]
            selected_company = st.selectbox(
                "Choose a Company",
                company_options,
                index=0
            )

            # Extract CIK from selection
            selected_cik = selected_company.split("CIK: ")[1].rstrip(")")

            # Option to add custom company name
            with st.expander("➕ Add Custom Company"):
                custom_name = st.text_input("Company Name")
                custom_cik = st.text_input("CIK Number")

                if st.button("Add to List"):
                    if custom_name and custom_cik:
                        if 'custom_companies' not in st.session_state:
                            st.session_state.custom_companies = []
                        st.session_state.custom_companies.append({
                            "name": custom_name,
                            "cik": custom_cik
                        })
                        st.success(f"Added {custom_name} (CIK: {custom_cik})")
                        st.rerun()
                    else:
                        st.error("Please provide both company name and CIK")

        else:  # Enter Custom CIK
            selected_cik = st.text_input(
                "Enter CIK Number",
                placeholder="e.g., 38777",
                help="Enter the Central Index Key (CIK) for the company"
            )

    with col2:
        st.info("""
        **What is CIK?**

        CIK (Central Index Key) is a unique identifier assigned by the SEC to companies filing documents.

        Find CIKs at:
        [SEC EDGAR Search](https://www.sec.gov/edgar/searchedgar/companysearch.html)
        """)

    st.markdown("---")

    # Query Parameters Section
    st.markdown("### ⚙️ Query Parameters")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Date Range**")

        # Quick date presets
        date_preset = st.selectbox(
            "Quick Select",
            ["Last 30 Days", "Last 90 Days", "Last 6 Months", "Last Year", "Last 2 Years", "Custom"],
            index=2
        )

        if date_preset == "Last 30 Days":
            start_date = (datetime.now() - timedelta(days=30)).date()
            end_date = datetime.now().date()
        elif date_preset == "Last 90 Days":
            start_date = (datetime.now() - timedelta(days=90)).date()
            end_date = datetime.now().date()
        elif date_preset == "Last 6 Months":
            start_date = (datetime.now() - timedelta(days=180)).date()
            end_date = datetime.now().date()
        elif date_preset == "Last Year":
            start_date = (datetime.now() - timedelta(days=365)).date()
            end_date = datetime.now().date()
        elif date_preset == "Last 2 Years":
            start_date = (datetime.now() - timedelta(days=730)).date()
            end_date = datetime.now().date()
        else:  # Custom
            start_date = st.date_input(
                "Start Date",
                value=(datetime.now() - timedelta(days=365)).date(),
                max_value=datetime.now().date()
            )
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )

    with col2:
        st.markdown("**Form Type**")

        # Form type selection
        form_type_selection = st.radio(
            "Selection",
            ["ABS Forms Only", "All Forms", "Custom Selection"],
            index=0
        )

        if form_type_selection == "ABS Forms Only":
            selected_form_types = ['ABS-EE', '10-D', 'ABS-15G']
        elif form_type_selection == "All Forms":
            selected_form_types = None
        else:  # Custom Selection
            selected_form_types = st.multiselect(
                "Select Form Types",
                ABS_FORM_TYPES,
                default=['ABS-EE', '10-D']
            )

    with col3:
        st.markdown("**Options**")

        max_results = st.number_input(
            "Max Results to Display",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            help="Maximum number of filings to display"
        )

        show_all_columns = st.checkbox(
            "Show All Columns",
            value=False,
            help="Display all available metadata columns"
        )

    st.markdown("---")

    # Query Button
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        query_button = st.button("🔍 Search SEC Filings", type="primary", use_container_width=True)

    with col2:
        if st.button("🔄 Clear Results", use_container_width=True):
            st.session_state.company_filings = None
            st.session_state.selected_filings = []
            st.rerun()

    # Execute Query
    if query_button and selected_cik:
        with st.spinner("Querying SEC EDGAR database..."):
            # Get company info first
            company_info = get_company_info(selected_cik)

            if company_info:
                st.success(f"Found company: {company_info.get('name', 'Unknown')}")

                # Get filings
                filings_df = get_company_filings(
                    cik=selected_cik,
                    form_types=selected_form_types,
                    start_date=start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime) else str(start_date),
                    end_date=end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else str(end_date)
                )

                if not filings_df.empty:
                    # Limit results
                    filings_df = filings_df.head(max_results)

                    # Add URLs
                    filings_df['url'] = filings_df.apply(
                        lambda row: get_filing_url(selected_cik, row['accessionNumber'], row['primaryDocument']),
                        axis=1
                    )

                    # Format file sizes
                    filings_df['sizeFormatted'] = filings_df['size'].apply(format_file_size)

                    st.session_state.company_filings = filings_df
                    st.session_state.selected_cik = selected_cik
                else:
                    st.warning("No filings found matching your criteria. Try adjusting the filters.")
            else:
                st.error("Could not retrieve company information. Please check the CIK number.")

    elif query_button and not selected_cik:
        st.error("Please select a company or enter a CIK number.")

    # Display Results
    if st.session_state.company_filings is not None and not st.session_state.company_filings.empty:
        df = st.session_state.company_filings

        st.markdown("---")
        st.markdown("### 📊 Available Filings")

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Filings", len(df))

        with col2:
            unique_forms = df['form'].nunique()
            st.metric("Unique Form Types", unique_forms)

        with col3:
            date_range_days = (pd.to_datetime(df['filingDate'].max()) - pd.to_datetime(df['filingDate'].min())).days
            st.metric("Date Range (days)", date_range_days)

        with col4:
            total_size = df['size'].sum()
            st.metric("Total Size", format_file_size(total_size))

        st.markdown("---")

        # Form type breakdown
        st.markdown("#### 📋 Breakdown by Form Type")

        form_counts = df['form'].value_counts()

        col1, col2 = st.columns([1, 2])

        with col1:
            for form_type, count in form_counts.items():
                st.write(f"**{form_type}**: {count} filings")

        with col2:
            import plotly.express as px
            fig = px.bar(
                x=form_counts.index,
                y=form_counts.values,
                labels={'x': 'Form Type', 'y': 'Number of Filings'},
                title="Filings by Form Type"
            )
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Filings table
        st.markdown("#### 📄 Filing Details")

        # Column selection
        if show_all_columns:
            display_cols = df.columns.tolist()
        else:
            display_cols = ['filingDate', 'form', 'primaryDocDescription', 'sizeFormatted', 'accessionNumber']
            display_cols = [col for col in display_cols if col in df.columns]

        # Display dataframe with selection
        st.dataframe(
            df[display_cols],
            use_container_width=True,
            height=400,
            hide_index=True,
            column_config={
                "filingDate": st.column_config.DateColumn("Filing Date", format="YYYY-MM-DD"),
                "sizeFormatted": st.column_config.TextColumn("File Size"),
                "form": st.column_config.TextColumn("Form Type"),
                "primaryDocDescription": st.column_config.TextColumn("Description"),
            }
        )

        st.markdown("---")

        # Download Options
        st.markdown("### 📥 Download Options")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("**Select filings to download:**")

            # Multi-select for filings
            filing_options = df.apply(
                lambda row: f"{row['filingDate']} - {row['form']} - {row['primaryDocDescription'][:50]}",
                axis=1
            ).tolist()

            selected_indices = st.multiselect(
                "Choose Filings",
                options=range(len(filing_options)),
                format_func=lambda x: filing_options[x],
                help="Select one or more filings to download"
            )

            if selected_indices:
                st.success(f"Selected {len(selected_indices)} filing(s)")

                # Show selected filings with links
                st.markdown("**Selected Filings:**")
                for idx in selected_indices:
                    row = df.iloc[idx]
                    st.markdown(f"- [{row['form']} - {row['filingDate']}]({row['url']}) ({row['sizeFormatted']})")

        with col2:
            st.markdown("**Quick Actions:**")

            # Export metadata to CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📊 Export Metadata (CSV)",
                data=csv,
                file_name=f"sec_filings_{st.session_state.selected_cik}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

            # Export metadata to JSON
            json_str = df.to_json(orient='records', date_format='iso', indent=2)
            st.download_button(
                label="📋 Export Metadata (JSON)",
                data=json_str,
                file_name=f"sec_filings_{st.session_state.selected_cik}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )

            if selected_indices:
                # Generate download script
                st.markdown("---")
                st.markdown("**Download Script:**")

                # Create a Python script to download selected filings
                script_lines = [
                    "import requests",
                    "import os",
                    "",
                    "# SEC filing URLs",
                    "filings = ["
                ]

                for idx in selected_indices:
                    row = df.iloc[idx]
                    script_lines.append(f"    '{row['url']}',")

                script_lines.extend([
                    "]",
                    "",
                    "# Download each filing",
                    "for url in filings:",
                    "    filename = url.split('/')[-1]",
                    "    print(f'Downloading {filename}...')",
                    "    response = requests.get(url)",
                    "    with open(filename, 'wb') as f:",
                    "        f.write(response.content)",
                    "    print(f'Saved {filename}')",
                ])

                script = "\n".join(script_lines)

                st.download_button(
                    label="🐍 Download Python Script",
                    data=script,
                    file_name=f"download_filings_{datetime.now().strftime('%Y%m%d')}.py",
                    mime="text/x-python",
                    use_container_width=True,
                    help="Download a Python script to fetch the selected filings"
                )

    # Help Section
    with st.expander("ℹ️ Help & Information"):
        st.markdown("""
        ### How to Use SEC Data Explorer

        1. **Select a Company**: Choose from default companies or enter a custom CIK number
        2. **Set Query Parameters**: Choose date range and form types
        3. **Search**: Click 'Search SEC Filings' to query the SEC EDGAR database
        4. **Review Results**: Browse the available filings and their metadata
        5. **Download**: Select specific filings and export metadata or download scripts

        ### About Form Types

        - **ABS-EE**: Asset-Backed Securities Informational and Computational Material
        - **10-D**: Asset-Backed Issuer Distribution Report
        - **ABS-15G**: Asset-Backed Securities Report
        - **10-K**: Annual Report
        - **10-Q**: Quarterly Report
        - **8-K**: Current Report (Material Events)

        ### Finding CIK Numbers

        You can find CIK numbers at the [SEC EDGAR Company Search](https://www.sec.gov/edgar/searchedgar/companysearch.html).

        ### Data Source

        All data is retrieved directly from the SEC EDGAR database via their public API.
        """)
