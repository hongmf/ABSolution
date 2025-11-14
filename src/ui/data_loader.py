"""
Data loader for ABSolution Streamlit dashboard
"""
import streamlit as st
import pandas as pd
import boto3
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class ABSDataLoader:
    """
    Data loader for ABS analytics dashboard.
    Handles data retrieval from DynamoDB, S3, and other AWS services.
    """

    def __init__(self, region: str = 'us-east-1'):
        """
        Initialize the data loader with AWS clients.

        Args:
            region: AWS region for services
        """
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.filings_table = self.dynamodb.Table('abs-filings')
        self.risk_scores_table = self.dynamodb.Table('abs-risk-scores')

    @st.cache_data(ttl=3600)
    def get_asset_classes(_self) -> List[str]:
        """
        Get list of unique asset classes from DynamoDB.

        Note: Using _self instead of self to prevent Streamlit from trying to hash
        the class instance, which would cause UnhashableParamError.

        Returns:
            List of asset class names
        """
        try:
            response = _self.filings_table.scan(
                ProjectionExpression='asset_class'
            )

            asset_classes = set()
            for item in response.get('Items', []):
                if 'asset_class' in item:
                    asset_classes.add(item['asset_class'])

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = _self.filings_table.scan(
                    ProjectionExpression='asset_class',
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                for item in response.get('Items', []):
                    if 'asset_class' in item:
                        asset_classes.add(item['asset_class'])

            return sorted(list(asset_classes))
        except Exception as e:
            st.error(f"Error fetching asset classes: {str(e)}")
            return []

    @st.cache_data(ttl=3600)
    def get_issuers(_self, asset_class: Optional[str] = None) -> List[str]:
        """
        Get list of unique issuers, optionally filtered by asset class.

        Args:
            asset_class: Optional asset class filter

        Returns:
            List of issuer names
        """
        try:
            scan_kwargs = {
                'ProjectionExpression': 'issuer_name'
            }

            if asset_class:
                scan_kwargs['FilterExpression'] = 'asset_class = :ac'
                scan_kwargs['ExpressionAttributeValues'] = {':ac': asset_class}

            response = _self.filings_table.scan(**scan_kwargs)

            issuers = set()
            for item in response.get('Items', []):
                if 'issuer_name' in item:
                    issuers.add(item['issuer_name'])

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = _self.filings_table.scan(**scan_kwargs)
                for item in response.get('Items', []):
                    if 'issuer_name' in item:
                        issuers.add(item['issuer_name'])

            return sorted(list(issuers))
        except Exception as e:
            st.error(f"Error fetching issuers: {str(e)}")
            return []

    @st.cache_data(ttl=600)
    def get_recent_filings(_self,
                          days: int = 30,
                          asset_class: Optional[str] = None,
                          issuer: Optional[str] = None) -> pd.DataFrame:
        """
        Get recent SEC filings with optional filters.

        Args:
            days: Number of days to look back
            asset_class: Optional asset class filter
            issuer: Optional issuer filter

        Returns:
            DataFrame with filing data
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            scan_kwargs = {
                'FilterExpression': 'filing_date >= :cutoff',
                'ExpressionAttributeValues': {':cutoff': cutoff_date}
            }

            # Add additional filters
            if asset_class:
                scan_kwargs['FilterExpression'] += ' AND asset_class = :ac'
                scan_kwargs['ExpressionAttributeValues'][':ac'] = asset_class

            if issuer:
                scan_kwargs['FilterExpression'] += ' AND issuer_name = :issuer'
                scan_kwargs['ExpressionAttributeValues'][':issuer'] = issuer

            response = _self.filings_table.scan(**scan_kwargs)
            items = response.get('Items', [])

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = _self.filings_table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))

            return pd.DataFrame(items)
        except Exception as e:
            st.error(f"Error fetching recent filings: {str(e)}")
            return pd.DataFrame()

    @st.cache_data(ttl=600)
    def get_risk_scores(_self,
                       filing_ids: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get risk scores for specified filings.

        Args:
            filing_ids: Optional list of filing IDs to fetch scores for

        Returns:
            DataFrame with risk score data
        """
        try:
            if filing_ids:
                # Batch get items for specific filing IDs
                items = []
                # DynamoDB batch_get_item has a limit of 100 items
                for i in range(0, len(filing_ids), 100):
                    batch = filing_ids[i:i+100]
                    response = _self.dynamodb.batch_get_item(
                        RequestItems={
                            'abs-risk-scores': {
                                'Keys': [{'filing_id': fid} for fid in batch]
                            }
                        }
                    )
                    items.extend(response.get('Responses', {}).get('abs-risk-scores', []))
            else:
                # Scan entire table
                response = _self.risk_scores_table.scan()
                items = response.get('Items', [])

                while 'LastEvaluatedKey' in response:
                    response = _self.risk_scores_table.scan(
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                    items.extend(response.get('Items', []))

            return pd.DataFrame(items)
        except Exception as e:
            st.error(f"Error fetching risk scores: {str(e)}")
            return pd.DataFrame()

    @st.cache_data(ttl=3600)
    def get_pool_statistics(_self,
                           asset_class: Optional[str] = None) -> pd.DataFrame:
        """
        Get aggregated pool statistics across filings.

        Args:
            asset_class: Optional asset class filter

        Returns:
            DataFrame with pool statistics
        """
        try:
            scan_kwargs = {}

            if asset_class:
                scan_kwargs['FilterExpression'] = 'asset_class = :ac'
                scan_kwargs['ExpressionAttributeValues'] = {':ac': asset_class}

            response = _self.filings_table.scan(**scan_kwargs)
            items = response.get('Items', [])

            while 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = _self.filings_table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))

            # Extract pool statistics
            pool_data = []
            for item in items:
                if 'pool_balance' in item:
                    pool_data.append({
                        'filing_id': item.get('filing_id'),
                        'issuer_name': item.get('issuer_name'),
                        'asset_class': item.get('asset_class'),
                        'pool_balance': float(item.get('pool_balance', 0)),
                        'weighted_avg_coupon': float(item.get('weighted_avg_coupon', 0)),
                        'weighted_avg_maturity': float(item.get('weighted_avg_maturity', 0)),
                        'delinquency_rate': float(item.get('delinquency_rate', 0)),
                        'filing_date': item.get('filing_date')
                    })

            return pd.DataFrame(pool_data)
        except Exception as e:
            st.error(f"Error fetching pool statistics: {str(e)}")
            return pd.DataFrame()

    def clear_cache(_self):
        """Clear all cached data."""
        st.cache_data.clear()
