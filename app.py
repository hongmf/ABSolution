"""
ABSolution - AWS-Native ABS Analytics Platform
Streamlit UI Main Application
"""

import streamlit as st
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="ABSolution - ABS Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 2rem;
        font-size: 1.1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📊 ABSolution</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AWS-Native Asset-Backed Securities Analytics Platform</div>', unsafe_allow_html=True)

# Initialize session state
if 'data_loader' not in st.session_state:
    from src.ui.data_loader import ABSDataLoader
    st.session_state.data_loader = ABSDataLoader(use_mock_data=True)

if 'filters' not in st.session_state:
    st.session_state.filters = {
        'start_date': datetime.now() - timedelta(days=90),
        'end_date': datetime.now(),
        'asset_class': 'All',
        'form_type': 'All',
        'company': None
    }

# Create tabs for Data and Analytics
tab1, tab2 = st.tabs(["📋 Data", "📈 Analytics"])

# Import page modules
from src.ui.pages import data_panel, analytics_panel

# Data Tab
with tab1:
    data_panel.render(st.session_state.data_loader, st.session_state.filters)

# Analytics Tab
with tab2:
    analytics_panel.render(st.session_state.data_loader, st.session_state.filters)

# Sidebar
with st.sidebar:
    st.markdown("### About ABSolution")
    st.markdown("""
    ABSolution is an AWS-native platform for analyzing Asset-Backed Securities (ABS) data.

    **Features:**
    - 📊 Real-time SEC filing ingestion
    - 🤖 AI-powered risk scoring
    - 📈 Advanced analytics & benchmarking
    - 🔍 Natural language insights

    **Powered by:**
    - AWS Glue & Kinesis
    - Amazon SageMaker
    - Amazon Bedrock
    - Amazon Comprehend
    """)

    st.markdown("---")

    st.markdown("### Data Source")
    use_mock = st.checkbox("Use Mock Data", value=True, help="Toggle between mock data and AWS data")

    if use_mock != st.session_state.data_loader.use_mock_data:
        st.session_state.data_loader.use_mock_data = use_mock
        st.rerun()

    st.markdown("---")

    st.markdown("### System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Status", "🟢 Online")
    with col2:
        st.metric("Mode", "Mock" if use_mock else "AWS")

    # Clear cache button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.success("Data cache cleared!")
        st.rerun()
