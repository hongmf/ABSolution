"""
ABSDataLoader: Data loading and caching layer for the ABSolution Streamlit UI.

This module provides cached data access methods for ABS analytics,
using Streamlit's caching mechanism with proper handling of instance methods.
"""

import streamlit as st
import pandas as pd
import boto3
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta


class ABSDataLoader:
    """
    Data loader for ABS (Asset-Backed Securities) analytics.

    Provides cached methods for loading and accessing ABS data from AWS services.
    All cached methods use '_self' parameter to avoid UnhashableParamError.
    """

    def __init__(self, s3_bucket: str, region: str = 'us-east-1'):
        """
        Initialize the ABSDataLoader.

        Args:
            s3_bucket: S3 bucket containing normalized ABS data
            region: AWS region for services
        """
        self.s3_bucket = s3_bucket
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        self.athena_client = boto3.client('athena', region_name=region)

    @st.cache_data(ttl=3600)
    def get_asset_classes(_self) -> List[str]:
        """
        Get list of available asset classes.

        Note: Uses '_self' instead of 'self' to avoid Streamlit UnhashableParamError.

        Returns:
            List of asset class names
        """
        # Query from S3 or Athena
        query = """
        SELECT DISTINCT asset_class
        FROM abs_normalized
        ORDER BY asset_class
        """
        results = _self._execute_athena_query(query)
        return [row['asset_class'] for row in results]

    @st.cache_data(ttl=3600)
    def get_issuers(_self, asset_class: Optional[str] = None) -> List[str]:
        """
        Get list of issuers, optionally filtered by asset class.

        Args:
            asset_class: Optional asset class filter

        Returns:
            List of issuer names
        """
        query = """
        SELECT DISTINCT issuer_name
        FROM abs_normalized
        """
        if asset_class:
            query += f" WHERE asset_class = '{asset_class}'"
        query += " ORDER BY issuer_name"

        results = _self._execute_athena_query(query)
        return [row['issuer_name'] for row in results]

    @st.cache_data(ttl=1800)
    def get_performance_metrics(_self, issuer: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get performance metrics for a specific issuer over a date range.

        Args:
            issuer: Issuer name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with performance metrics
        """
        query = f"""
        SELECT
            filing_date,
            delinquency_rate,
            default_rate,
            prepayment_rate,
            average_fico,
            pool_balance,
            weighted_avg_coupon
        FROM abs_performance
        WHERE issuer_name = '{issuer}'
          AND filing_date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY filing_date
        """

        results = _self._execute_athena_query(query)
        return pd.DataFrame(results)

    @st.cache_data(ttl=1800)
    def get_risk_scores(_self, asset_class: Optional[str] = None) -> pd.DataFrame:
        """
        Get latest risk scores for issuers.

        Args:
            asset_class: Optional asset class filter

        Returns:
            DataFrame with risk scores
        """
        query = """
        SELECT
            issuer_name,
            asset_class,
            risk_score,
            risk_category,
            last_updated
        FROM risk_scores
        WHERE is_latest = true
        """
        if asset_class:
            query += f" AND asset_class = '{asset_class}'"
        query += " ORDER BY risk_score DESC"

        results = _self._execute_athena_query(query)
        return pd.DataFrame(results)

    @st.cache_data(ttl=3600)
    def get_trend_analysis(_self, issuer: str, metric: str) -> Dict[str, Any]:
        """
        Get trend analysis for a specific issuer and metric.

        Args:
            issuer: Issuer name
            metric: Metric name (e.g., 'delinquency_rate', 'fico_score')

        Returns:
            Dictionary with trend analysis results
        """
        # Get historical data
        query = f"""
        SELECT filing_date, {metric}
        FROM abs_performance
        WHERE issuer_name = '{issuer}'
        ORDER BY filing_date DESC
        LIMIT 12
        """

        results = _self._execute_athena_query(query)
        df = pd.DataFrame(results)

        if len(df) < 2:
            return {
                'trend': 'insufficient_data',
                'change': 0,
                'current_value': None
            }

        # Calculate trend
        current = df[metric].iloc[0]
        previous = df[metric].iloc[1]
        change = ((current - previous) / previous * 100) if previous != 0 else 0

        return {
            'trend': 'increasing' if change > 0 else 'decreasing' if change < 0 else 'stable',
            'change': change,
            'current_value': current,
            'historical_data': df.to_dict('records')
        }

    @st.cache_data(ttl=3600)
    def get_benchmark_comparison(_self, issuer: str, asset_class: str) -> Dict[str, Any]:
        """
        Compare an issuer's metrics against asset class benchmarks.

        Args:
            issuer: Issuer name
            asset_class: Asset class for benchmark

        Returns:
            Dictionary with comparison data
        """
        query = f"""
        WITH issuer_metrics AS (
            SELECT
                AVG(delinquency_rate) as avg_delinquency,
                AVG(default_rate) as avg_default,
                AVG(prepayment_rate) as avg_prepayment
            FROM abs_performance
            WHERE issuer_name = '{issuer}'
              AND filing_date >= DATE_ADD('month', -12, CURRENT_DATE)
        ),
        benchmark AS (
            SELECT
                AVG(delinquency_rate) as bench_delinquency,
                AVG(default_rate) as bench_default,
                AVG(prepayment_rate) as bench_prepayment
            FROM abs_performance
            WHERE asset_class = '{asset_class}'
              AND filing_date >= DATE_ADD('month', -12, CURRENT_DATE)
        )
        SELECT * FROM issuer_metrics, benchmark
        """

        results = _self._execute_athena_query(query)
        if results:
            return results[0]
        return {}

    @st.cache_data(ttl=600)
    def get_recent_filings(_self, limit: int = 10) -> pd.DataFrame:
        """
        Get most recent SEC filings.

        Args:
            limit: Number of recent filings to retrieve

        Returns:
            DataFrame with recent filings
        """
        query = f"""
        SELECT
            issuer_name,
            filing_type,
            filing_date,
            sentiment_score,
            key_topics
        FROM sec_filings
        ORDER BY filing_date DESC
        LIMIT {limit}
        """

        results = _self._execute_athena_query(query)
        return pd.DataFrame(results)

    @st.cache_data(ttl=1800)
    def get_ai_insights(_self, issuer: str) -> str:
        """
        Get AI-generated narrative insights for an issuer using Bedrock.

        Args:
            issuer: Issuer name

        Returns:
            Narrative insight text
        """
        # Get issuer data for context
        performance_data = _self.get_performance_metrics(
            issuer,
            (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            datetime.now().strftime('%Y-%m-%d')
        )

        risk_data = _self.get_risk_scores()
        issuer_risk = risk_data[risk_data['issuer_name'] == issuer]

        # This would call Amazon Bedrock in production
        # For now, return a placeholder
        insight = f"Analysis for {issuer}: "

        if not performance_data.empty:
            latest_delinq = performance_data['delinquency_rate'].iloc[-1]
            insight += f"Current delinquency rate at {latest_delinq:.2f}%. "

        if not issuer_risk.empty:
            risk_score = issuer_risk['risk_score'].iloc[0]
            insight += f"Risk score: {risk_score}. "

        return insight

    def _execute_athena_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute an Athena query and return results.

        Args:
            query: SQL query to execute

        Returns:
            List of result rows as dictionaries
        """
        # In production, this would execute the Athena query
        # For now, return mock data
        return []

    @st.cache_data(ttl=3600)
    def get_loan_pool_details(_self, issuer: str, pool_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific loan pool.

        Args:
            issuer: Issuer name
            pool_id: Loan pool identifier

        Returns:
            Dictionary with pool details
        """
        query = f"""
        SELECT
            pool_id,
            pool_balance,
            number_of_loans,
            weighted_avg_fico,
            weighted_avg_ltv,
            weighted_avg_rate,
            geographic_concentration,
            vintage
        FROM loan_pools
        WHERE issuer_name = '{issuer}'
          AND pool_id = '{pool_id}'
        """

        results = _self._execute_athena_query(query)
        return results[0] if results else {}

    @st.cache_data(ttl=3600)
    def get_alerts(_self, severity: Optional[str] = None) -> pd.DataFrame:
        """
        Get active alerts for risk thresholds.

        Args:
            severity: Optional filter by severity (critical, warning, info)

        Returns:
            DataFrame with active alerts
        """
        query = """
        SELECT
            alert_id,
            issuer_name,
            alert_type,
            severity,
            message,
            created_at
        FROM alerts
        WHERE status = 'active'
        """
        if severity:
            query += f" AND severity = '{severity}'"
        query += " ORDER BY created_at DESC"

        results = _self._execute_athena_query(query)
        return pd.DataFrame(results)
