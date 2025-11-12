"""
Data Loader for Streamlit UI
Handles data retrieval from AWS services (DynamoDB, S3) with caching
"""

import boto3
import pandas as pd
import json
import streamlit as st
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """Helper to convert Decimal to float for JSON serialization"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class ABSDataLoader:
    """Loads ABS filing data from AWS services"""

    def __init__(self, use_mock_data=False):
        """
        Initialize data loader

        Args:
            use_mock_data: If True, use mock data instead of AWS
        """
        self.use_mock_data = use_mock_data

        if not use_mock_data:
            try:
                self.dynamodb = boto3.resource('dynamodb')
                self.s3_client = boto3.client('s3')
                self.filings_table = self.dynamodb.Table('abs-filings')
                self.risk_table = self.dynamodb.Table('abs-risk-scores')
            except Exception as e:
                logger.warning(f"Could not connect to AWS: {e}. Using mock data.")
                self.use_mock_data = True

    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_filings(_self,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   asset_class: Optional[str] = None,
                   form_type: Optional[str] = None,
                   cik: Optional[str] = None) -> pd.DataFrame:
        """
        Load SEC filings with filters

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            asset_class: Filter by asset class
            form_type: Filter by form type
            cik: Filter by CIK

        Returns:
            DataFrame with filing data
        """
        if _self.use_mock_data:
            return _self._get_mock_filings(start_date, end_date, asset_class, form_type, cik)

        try:
            # Build filter expression
            filter_expressions = []

            if start_date:
                filter_expressions.append(f"filing_date >= :start_date")
            if end_date:
                filter_expressions.append(f"filing_date <= :end_date")
            if asset_class and asset_class != "All":
                filter_expressions.append(f"asset_class = :asset_class")
            if form_type and form_type != "All":
                filter_expressions.append(f"form_type = :form_type")
            if cik:
                filter_expressions.append(f"cik = :cik")

            # Query DynamoDB
            scan_kwargs = {}
            if filter_expressions:
                from boto3.dynamodb.conditions import Attr
                filter_expr = None
                for expr in filter_expressions:
                    condition = None
                    if "start_date" in expr:
                        condition = Attr('filing_date').gte(start_date)
                    elif "end_date" in expr:
                        condition = Attr('filing_date').lte(end_date)
                    elif "asset_class" in expr:
                        condition = Attr('asset_class').eq(asset_class)
                    elif "form_type" in expr:
                        condition = Attr('form_type').eq(form_type)
                    elif "cik" in expr:
                        condition = Attr('cik').eq(cik)

                    if condition:
                        filter_expr = condition if filter_expr is None else filter_expr & condition

                if filter_expr:
                    scan_kwargs['FilterExpression'] = filter_expr

            response = _self.filings_table.scan(**scan_kwargs)
            items = response.get('Items', [])

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = _self.filings_table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))

            # Convert to DataFrame
            df = pd.DataFrame(items)

            # Convert Decimal to float
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)

            return df

        except Exception as e:
            logger.error(f"Error loading filings: {e}")
            return _self._get_mock_filings(start_date, end_date, asset_class, form_type, cik)

    def _get_mock_filings(_self, start_date=None, end_date=None, asset_class=None, form_type=None, cik=None) -> pd.DataFrame:
        """Generate mock filing data for testing"""
        import numpy as np
        from datetime import datetime, timedelta

        # Generate dates
        base_date = datetime.now() - timedelta(days=365)
        dates = [base_date + timedelta(days=x) for x in range(0, 365, 7)]

        # Asset classes and companies
        asset_classes = ['AUTO_LOAN', 'CREDIT_CARD', 'STUDENT_LOAN', 'MORTGAGE']
        companies = [
            ('0001467858', 'GM Financial'),
            ('0000038009', 'Ford Credit'),
            ('0001548357', 'Santander Consumer'),
            ('0001234570', 'Bank of America Mortgage'),
            ('0001234571', 'Ally Auto Receivables'),
            ('0001234572', 'Discover Card Trust'),
        ]
        form_types = ['ABS-EE', '10-D', '10-K', '8-K']

        # Generate mock data
        data = []
        for date in dates:
            for company_cik, company_name in companies:
                # Determine asset class based on company
                if any(x in company_name for x in ['GM Financial', 'Ford Credit', 'Santander Consumer', 'Ally', 'Auto']):
                    co_asset_class = 'AUTO_LOAN'
                elif 'Card' in company_name or 'Discover' in company_name:
                    co_asset_class = 'CREDIT_CARD'
                elif 'Student' in company_name:
                    co_asset_class = 'STUDENT_LOAN'
                else:
                    co_asset_class = 'MORTGAGE'

                filing = {
                    'filing_id': f"{company_cik}{date.strftime('%Y%m%d')}",
                    'accession_number': f"0001234567-{date.strftime('%y-%m%d')}",
                    'cik': company_cik,
                    'company_name': company_name,
                    'issuer_name': company_name,
                    'form_type': np.random.choice(form_types),
                    'filing_date': date.strftime('%Y-%m-%d'),
                    'filing_year': date.year,
                    'filing_quarter': (date.month - 1) // 3 + 1,
                    'asset_class': co_asset_class,
                    'deal_name': f"{company_name} Series {date.strftime('%Y-%m')}",

                    # Financial metrics
                    'original_pool_balance': np.random.uniform(500000000, 2000000000),
                    'current_pool_balance': np.random.uniform(300000000, 1500000000),
                    'total_principal_received': np.random.uniform(100000000, 500000000),

                    # Performance metrics
                    'delinquency_30_days': np.random.uniform(0.01, 0.05),
                    'delinquency_60_days': np.random.uniform(0.005, 0.03),
                    'delinquency_90_plus_days': np.random.uniform(0.002, 0.02),
                    'cumulative_default_rate': np.random.uniform(0.01, 0.08),
                    'cumulative_loss_rate': np.random.uniform(0.005, 0.04),

                    # Credit metrics
                    'weighted_average_fico': int(np.random.uniform(650, 750)),
                    'weighted_average_ltv': np.random.uniform(0.6, 0.9),
                    'weighted_average_dti': np.random.uniform(0.3, 0.5),

                    'data_quality_score': np.random.uniform(0.7, 1.0),
                    'processed_at': date.isoformat(),
                }
                data.append(filing)

        df = pd.DataFrame(data)

        # Apply filters
        if start_date:
            df = df[df['filing_date'] >= start_date]
        if end_date:
            df = df[df['filing_date'] <= end_date]
        if asset_class and asset_class != "All":
            df = df[df['asset_class'] == asset_class]
        if form_type and form_type != "All":
            df = df[df['form_type'] == form_type]
        if cik:
            df = df[df['cik'] == cik]

        return df

    @st.cache_data(ttl=300)
    def get_risk_scores(_self, cik: Optional[str] = None, asset_class: Optional[str] = None) -> pd.DataFrame:
        """
        Load risk scores with filters

        Args:
            cik: Filter by CIK
            asset_class: Filter by asset class

        Returns:
            DataFrame with risk scores
        """
        if _self.use_mock_data:
            return _self._get_mock_risk_scores(cik, asset_class)

        try:
            scan_kwargs = {}

            if cik or asset_class:
                from boto3.dynamodb.conditions import Attr
                filter_expr = None

                if cik:
                    filter_expr = Attr('cik').eq(cik)
                if asset_class and asset_class != "All":
                    condition = Attr('asset_class').eq(asset_class)
                    filter_expr = condition if filter_expr is None else filter_expr & condition

                if filter_expr:
                    scan_kwargs['FilterExpression'] = filter_expr

            response = _self.risk_table.scan(**scan_kwargs)
            items = response.get('Items', [])

            df = pd.DataFrame(items)

            # Convert Decimal to float
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)

            return df

        except Exception as e:
            logger.error(f"Error loading risk scores: {e}")
            return _self._get_mock_risk_scores(cik, asset_class)

    def _get_mock_risk_scores(_self, cik=None, asset_class=None) -> pd.DataFrame:
        """Generate mock risk score data"""
        import numpy as np

        # Get filings to generate risk scores
        filings_df = _self._get_mock_filings(cik=cik, asset_class=asset_class)

        if filings_df.empty:
            return pd.DataFrame()

        # Generate risk scores for each filing
        risk_data = []
        for _, filing in filings_df.iterrows():
            risk_score = np.random.uniform(0, 100)

            if risk_score < 30:
                risk_level = 'LOW'
            elif risk_score < 60:
                risk_level = 'MEDIUM'
            elif risk_score < 80:
                risk_level = 'HIGH'
            else:
                risk_level = 'CRITICAL'

            risk_data.append({
                'filing_id': filing['filing_id'],
                'cik': filing['cik'],
                'company_name': filing['company_name'],
                'asset_class': filing['asset_class'],
                'risk_score': risk_score,
                'risk_level': risk_level,
                'delinquency_risk': np.random.uniform(0, 100),
                'default_risk': np.random.uniform(0, 100),
                'liquidity_risk': np.random.uniform(0, 100),
                'scored_at': filing['filing_date']
            })

        return pd.DataFrame(risk_data)

    @st.cache_data(ttl=600)
    def get_unique_companies(_self) -> List[Dict[str, str]]:
        """Get list of unique companies (CIK and name)"""
        df = _self.get_filings()
        if df.empty:
            return []

        companies = df[['cik', 'company_name']].drop_duplicates()
        return companies.to_dict('records')

    @st.cache_data(ttl=600)
    def get_asset_classes(_self) -> List[str]:
        """Get list of unique asset classes"""
        df = _self.get_filings()
        if df.empty:
            return []

        return sorted(df['asset_class'].unique().tolist())

    @st.cache_data(ttl=600)
    def get_form_types(_self) -> List[str]:
        """Get list of unique form types"""
        df = _self.get_filings()
        if df.empty:
            return []

        return sorted(df['form_type'].unique().tolist())
