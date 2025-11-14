"""
ABS Data Loader Utility
Provides utilities for loading ABS filing data for testing and development
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ABSDataLoader:
    """Utility class for loading ABS filing data"""

    def __init__(self):
        self.asset_classes = ['AUTO_LOAN', 'CREDIT_CARD', 'STUDENT_LOAN', 'MORTGAGE']

    def _get_mock_filings(self, cik: Optional[str] = None, count: int = 10) -> List[Dict]:
        """
        Generate mock SEC filings for testing

        Args:
            cik: Central Index Key for filtering filings (optional)
            count: Number of mock filings to generate

        Returns:
            List of mock filing dictionaries
        """
        filings = []

        for i in range(count):
            # Use provided CIK or generate random one
            filing_cik = cik if cik else f"{random.randint(1000000, 9999999):07d}"

            filing = self._generate_single_filing(filing_cik)
            filings.append(filing)

        logger.info(f"Generated {len(filings)} mock filings" + (f" for CIK {cik}" if cik else ""))
        return filings

    def _generate_single_filing(self, cik: str) -> Dict:
        """
        Generate a single mock filing

        Args:
            cik: Central Index Key for the filing

        Returns:
            Mock filing dictionary
        """
        asset_class = random.choice(self.asset_classes)

        filing = {
            'accessionNo': f"0001234567-{datetime.utcnow().strftime('%y-%m%d')}-{random.randint(1000, 9999)}",
            'cik': cik,
            'companyName': f"Example Issuer {cik[-4:]} LLC",
            'formType': random.choice(['ABS-EE', '10-D', '10-K', '8-K']),
            'filedAt': (datetime.utcnow() - timedelta(days=random.randint(0, 90))).isoformat(),
            'fiscalYear': datetime.utcnow().year,
            'fiscalPeriod': f"Q{(datetime.utcnow().month-1)//3 + 1}",

            'deal': {
                'name': f"{asset_class.replace('_', ' ')} Trust {datetime.utcnow().year}-{random.randint(1, 5)}"
            },

            'issuer': {
                'name': f"Example Issuer {cik[-4:]} LLC"
            },

            'poolStats': {
                'originalBalance': random.uniform(500000000, 2000000000),
                'currentBalance': random.uniform(300000000, 1500000000),
                'principalReceived': random.uniform(100000000, 500000000)
            },

            'performance': {
                'delinquency30': random.uniform(0.01, 0.05),
                'delinquency60': random.uniform(0.005, 0.03),
                'delinquency90Plus': random.uniform(0.002, 0.02),
                'cumulativeDefaultRate': random.uniform(0.01, 0.08),
                'cumulativeLossRate': random.uniform(0.005, 0.05)
            },

            'creditMetrics': {
                'avgFICO': random.randint(620, 760),
                'avgLTV': random.uniform(0.60, 0.85),
                'avgDTI': random.uniform(0.25, 0.45)
            },

            'description': f"{asset_class.replace('_', ' ')} backed securities"
        }

        return filing

    def get_mock_filings_by_cik(self, cik: str, count: int = 10) -> List[Dict]:
        """
        Get mock filings for a specific CIK

        Args:
            cik: Central Index Key
            count: Number of filings to generate

        Returns:
            List of mock filings for the specified CIK
        """
        return self._get_mock_filings(cik=cik, count=count)

    def get_mock_filings_by_asset_class(self, asset_class: str, count: int = 10) -> List[Dict]:
        """
        Get mock filings for a specific asset class

        Args:
            asset_class: Asset class (e.g., 'AUTO_LOAN', 'CREDIT_CARD')
            count: Number of filings to generate

        Returns:
            List of mock filings for the specified asset class
        """
        if asset_class not in self.asset_classes:
            raise ValueError(f"Invalid asset class. Must be one of: {self.asset_classes}")

        # Temporarily set asset_classes to only the requested one
        original_asset_classes = self.asset_classes
        self.asset_classes = [asset_class]

        filings = self._get_mock_filings(count=count)

        # Restore original asset_classes
        self.asset_classes = original_asset_classes

        return filings

    def load_filings_from_json(self, file_path: str) -> List[Dict]:
        """
        Load filings from a JSON file

        Args:
            file_path: Path to JSON file containing filings

        Returns:
            List of filing dictionaries
        """
        try:
            with open(file_path, 'r') as f:
                filings = json.load(f)

            logger.info(f"Loaded {len(filings)} filings from {file_path}")
            return filings

        except Exception as e:
            logger.error(f"Error loading filings from {file_path}: {str(e)}")
            raise

    def save_filings_to_json(self, filings: List[Dict], file_path: str):
        """
        Save filings to a JSON file

        Args:
            filings: List of filing dictionaries
            file_path: Path to save JSON file
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(filings, f, indent=2, default=str)

            logger.info(f"Saved {len(filings)} filings to {file_path}")

        except Exception as e:
            logger.error(f"Error saving filings to {file_path}: {str(e)}")
            raise


# Example usage
if __name__ == '__main__':
    loader = ABSDataLoader()

    # Generate mock filings for a specific CIK
    cik = "0001234567"
    filings = loader.get_mock_filings_by_cik(cik, count=5)
    print(f"Generated {len(filings)} filings for CIK {cik}")

    # Generate mock filings for AUTO_LOAN asset class
    auto_filings = loader.get_mock_filings_by_asset_class('AUTO_LOAN', count=3)
    print(f"Generated {len(auto_filings)} AUTO_LOAN filings")

    # Save to file
    loader.save_filings_to_json(filings, '/tmp/mock_filings.json')
