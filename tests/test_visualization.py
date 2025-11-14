"""
Tests for visualization module
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.visualization import plot_utils
from src.visualization.data_loader import generate_sample_data


class TestPlotUtils:
    """Test plot utility functions"""

    @pytest.fixture
    def sample_risk_data(self):
        """Generate sample risk score data"""
        return pd.DataFrame({
            'risk_score': np.random.beta(2, 5, 100),
            'filing_id': [f'filing_{i:06d}' for i in range(100)]
        })

    @pytest.fixture
    def sample_delinquency_data(self):
        """Generate sample delinquency data"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        return pd.DataFrame({
            'filing_date': dates,
            'delinquency_rate': np.random.beta(2, 10, 100)
        })

    @pytest.fixture
    def sample_asset_class_data(self):
        """Generate sample asset class data"""
        return pd.DataFrame({
            'asset_class': ['Auto', 'Credit Card', 'Student Loan', 'Equipment', 'Mortgage'],
            'avg_risk_score': np.random.uniform(0.2, 0.6, 5),
            'avg_delinquency_rate': np.random.uniform(0.05, 0.15, 5)
        })

    @pytest.fixture
    def sample_issuer_data(self):
        """Generate sample issuer data"""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='W')
        issuers = ['Issuer A', 'Issuer B', 'Issuer C']
        data = []
        for issuer in issuers:
            for date in dates:
                data.append({
                    'issuer_name': issuer,
                    'filing_date': date,
                    'risk_score': np.random.beta(2, 5),
                    'delinquency_rate': np.random.beta(2, 10),
                    'fico_score': np.random.normal(700, 50),
                    'pool_balance': np.random.uniform(1e7, 1e9)
                })
        return pd.DataFrame(data)

    def test_create_risk_score_distribution(self, sample_risk_data):
        """Test risk score distribution plot creation"""
        fig = plot_utils.create_risk_score_distribution(sample_risk_data)
        assert fig is not None
        assert len(fig.data) > 0
        assert fig.layout.xaxis.title.text == "Risk Score"
        assert fig.layout.yaxis.title.text == "Count"

    def test_create_delinquency_trends(self, sample_delinquency_data):
        """Test delinquency trends plot creation"""
        fig = plot_utils.create_delinquency_trends(sample_delinquency_data)
        assert fig is not None
        assert len(fig.data) > 0
        assert fig.layout.xaxis.title.text == "Date"

    def test_create_asset_class_comparison(self, sample_asset_class_data):
        """Test asset class comparison plot creation"""
        fig = plot_utils.create_asset_class_comparison(sample_asset_class_data)
        assert fig is not None
        assert len(fig.data) == 2  # Two bar charts

    def test_create_issuer_performance(self, sample_issuer_data):
        """Test issuer performance plot creation"""
        issuer_data = sample_issuer_data[sample_issuer_data['issuer_name'] == 'Issuer A']
        fig = plot_utils.create_issuer_performance(issuer_data, issuer_name='Issuer A')
        assert fig is not None
        assert len(fig.data) > 0

    def test_create_risk_timeline(self, sample_issuer_data):
        """Test risk timeline plot creation"""
        fig = plot_utils.create_risk_timeline(sample_issuer_data)
        assert fig is not None
        assert len(fig.data) > 0

    def test_create_top_risk_issuers(self, sample_issuer_data):
        """Test top risk issuers plot creation"""
        fig = plot_utils.create_top_risk_issuers(sample_issuer_data, top_n=5)
        assert fig is not None
        assert len(fig.data) > 0


class TestDataLoader:
    """Test data loader functions"""

    def test_generate_sample_data(self):
        """Test sample data generation"""
        data = generate_sample_data(n_records=100, n_issuers=5)

        # Check all expected datasets are present
        assert 'risk_scores' in data
        assert 'delinquencies' in data
        assert 'issuers' in data
        assert 'asset_classes' in data

        # Check data types
        assert isinstance(data['risk_scores'], pd.DataFrame)
        assert isinstance(data['delinquencies'], pd.DataFrame)
        assert isinstance(data['issuers'], pd.DataFrame)
        assert isinstance(data['asset_classes'], pd.DataFrame)

        # Check data shapes
        assert len(data['risk_scores']) == 100
        assert len(data['delinquencies']) == 100
        assert len(data['issuers']) > 0
        assert len(data['asset_classes']) == 5

        # Check required columns
        assert 'risk_score' in data['risk_scores'].columns
        assert 'filing_date' in data['risk_scores'].columns
        assert 'delinquency_rate' in data['delinquencies'].columns
        assert 'issuer_name' in data['issuers'].columns
        assert 'asset_class' in data['asset_classes'].columns

    def test_sample_data_values(self):
        """Test that sample data has realistic values"""
        data = generate_sample_data(n_records=100, n_issuers=5)

        # Risk scores should be between 0 and 1
        assert data['risk_scores']['risk_score'].min() >= 0
        assert data['risk_scores']['risk_score'].max() <= 1

        # Delinquency rates should be between 0 and 1
        assert data['delinquencies']['delinquency_rate'].min() >= 0
        assert data['delinquencies']['delinquency_rate'].max() <= 1

        # FICO scores should be in valid range
        assert data['issuers']['fico_score'].min() >= 300
        assert data['issuers']['fico_score'].max() <= 850

        # Pool balances should be positive
        assert data['issuers']['pool_balance'].min() > 0

    def test_sample_data_dates(self):
        """Test that dates are generated correctly"""
        data = generate_sample_data(n_records=100, n_issuers=5)

        # Check dates are datetime objects
        assert pd.api.types.is_datetime64_any_dtype(data['risk_scores']['filing_date'])
        assert pd.api.types.is_datetime64_any_dtype(data['delinquencies']['filing_date'])
        assert pd.api.types.is_datetime64_any_dtype(data['issuers']['filing_date'])

        # Check dates are sorted
        assert data['risk_scores']['filing_date'].is_monotonic_increasing
        assert data['delinquencies']['filing_date'].is_monotonic_increasing


class TestComprehensiveDashboard:
    """Test comprehensive dashboard creation"""

    def test_create_comprehensive_dashboard(self):
        """Test creating all plots at once"""
        data = generate_sample_data(n_records=100, n_issuers=5)
        plots = plot_utils.create_comprehensive_dashboard(data)

        # Check that plots were created
        assert isinstance(plots, dict)
        assert len(plots) > 0

        # Check expected plots are present
        assert 'risk_distribution' in plots
        assert 'delinquency_trends' in plots
        assert 'asset_comparison' in plots
        assert 'risk_timeline' in plots
        assert 'top_risk_issuers' in plots

    def test_empty_data_handling(self):
        """Test that functions handle empty data gracefully"""
        empty_data = {
            'risk_scores': pd.DataFrame(),
            'delinquencies': pd.DataFrame(),
            'issuers': pd.DataFrame(),
            'asset_classes': pd.DataFrame()
        }

        plots = plot_utils.create_comprehensive_dashboard(empty_data)
        assert isinstance(plots, dict)
        # Should return empty dict for empty data
        assert len(plots) == 0


def test_imports():
    """Test that all imports work correctly"""
    from src.visualization import (
        create_risk_score_distribution,
        create_delinquency_trends,
        create_asset_class_comparison,
        create_issuer_performance,
        create_risk_timeline,
        create_top_risk_issuers
    )

    # If we get here, imports worked
    assert True


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v'])
