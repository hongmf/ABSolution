"""
Unit tests for ABSDataLoader
"""

import pytest
import json
from src.utils.data_loader import ABSDataLoader


class TestABSDataLoader:
    """Test cases for ABSDataLoader"""

    def setup_method(self):
        """Setup test fixtures"""
        self.loader = ABSDataLoader()

    def test_get_mock_filings_without_cik(self):
        """Test generating mock filings without CIK parameter"""
        filings = self.loader._get_mock_filings(count=5)

        assert len(filings) == 5
        assert all('cik' in filing for filing in filings)
        assert all('accessionNo' in filing for filing in filings)

    def test_get_mock_filings_with_cik(self):
        """Test generating mock filings with CIK parameter (fixes the TypeError)"""
        cik = "0001234567"
        filings = self.loader._get_mock_filings(cik=cik, count=3)

        assert len(filings) == 3
        # All filings should have the same CIK
        assert all(filing['cik'] == cik for filing in filings)

    def test_get_mock_filings_by_cik(self):
        """Test convenience method for getting filings by CIK"""
        cik = "0009876543"
        filings = self.loader.get_mock_filings_by_cik(cik, count=10)

        assert len(filings) == 10
        assert all(filing['cik'] == cik for filing in filings)
        assert all(filing['companyName'] for filing in filings)

    def test_get_mock_filings_by_asset_class(self):
        """Test getting mock filings filtered by asset class"""
        asset_class = 'AUTO_LOAN'
        filings = self.loader.get_mock_filings_by_asset_class(asset_class, count=5)

        assert len(filings) == 5
        # Check that all filings have AUTO_LOAN in description
        assert all('auto loan' in filing['description'].lower() for filing in filings)

    def test_invalid_asset_class(self):
        """Test that invalid asset class raises ValueError"""
        with pytest.raises(ValueError):
            self.loader.get_mock_filings_by_asset_class('INVALID_CLASS', count=5)

    def test_filing_structure(self):
        """Test that generated filings have the expected structure"""
        filings = self.loader._get_mock_filings(cik="0001111111", count=1)
        filing = filings[0]

        # Check required fields
        required_fields = [
            'accessionNo', 'cik', 'companyName', 'formType', 'filedAt',
            'fiscalYear', 'fiscalPeriod', 'deal', 'issuer', 'poolStats',
            'performance', 'creditMetrics', 'description'
        ]

        for field in required_fields:
            assert field in filing, f"Missing required field: {field}"

        # Check nested structures
        assert 'name' in filing['deal']
        assert 'name' in filing['issuer']
        assert 'originalBalance' in filing['poolStats']
        assert 'delinquency30' in filing['performance']
        assert 'avgFICO' in filing['creditMetrics']

    def test_filing_metrics_ranges(self):
        """Test that generated metrics are within expected ranges"""
        filings = self.loader._get_mock_filings(count=20)

        for filing in filings:
            # Check FICO scores are reasonable
            fico = filing['creditMetrics']['avgFICO']
            assert 620 <= fico <= 760, f"FICO score {fico} out of range"

            # Check delinquency rates are proportions
            perf = filing['performance']
            assert 0 <= perf['delinquency30'] <= 1
            assert 0 <= perf['delinquency60'] <= 1
            assert 0 <= perf['delinquency90Plus'] <= 1

            # Check LTV and DTI are proportions
            assert 0 <= filing['creditMetrics']['avgLTV'] <= 1
            assert 0 <= filing['creditMetrics']['avgDTI'] <= 1

    def test_save_and_load_filings(self, tmp_path):
        """Test saving and loading filings to/from JSON"""
        # Generate filings
        cik = "0001234567"
        original_filings = self.loader.get_mock_filings_by_cik(cik, count=5)

        # Save to temporary file
        file_path = tmp_path / "test_filings.json"
        self.loader.save_filings_to_json(original_filings, str(file_path))

        # Load back
        loaded_filings = self.loader.load_filings_from_json(str(file_path))

        # Verify
        assert len(loaded_filings) == len(original_filings)
        assert loaded_filings[0]['cik'] == cik

    def test_multiple_ciks(self):
        """Test that filings without CIK have different CIKs"""
        filings = self.loader._get_mock_filings(count=10)

        ciks = [filing['cik'] for filing in filings]
        # Should have multiple unique CIKs (random generation)
        assert len(set(ciks)) >= 5, "Expected diverse CIK generation"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
