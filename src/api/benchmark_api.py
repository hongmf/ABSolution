"""
Benchmark API - Lambda Handler
Expose API for external teams to query issuer benchmarks and ABS analytics
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Environment variables
FILINGS_TABLE = os.environ.get('FILINGS_TABLE', 'abs-filings')
RISK_TABLE = os.environ.get('RISK_TABLE', 'abs-risk-scores')


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal to JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class BenchmarkAPI:
    """ABS Benchmark API Handler"""

    def __init__(self):
        self.filings_table = dynamodb.Table(FILINGS_TABLE)
        self.risk_table = dynamodb.Table(RISK_TABLE)

    def get_issuer_benchmark(self, cik, lookback_days=90):
        """
        Get benchmark metrics for a specific issuer

        Args:
            cik: Central Index Key for the issuer
            lookback_days: Number of days to look back for data

        Returns:
            Benchmark metrics dictionary
        """
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=lookback_days)).isoformat()

            # Query filings
            response = self.filings_table.query(
                IndexName='cik-filing_date-index',
                KeyConditionExpression=Key('cik').eq(cik) & Key('filing_date').gte(cutoff_date)
            )

            filings = response.get('Items', [])

            if not filings:
                return {
                    'error': 'No data found for issuer',
                    'cik': cik
                }

            # Calculate benchmarks
            benchmark = self._calculate_benchmarks(filings)
            benchmark['cik'] = cik
            benchmark['company_name'] = filings[0].get('company_name')
            benchmark['data_points'] = len(filings)
            benchmark['lookback_days'] = lookback_days

            return benchmark

        except Exception as e:
            logger.error(f"Error getting issuer benchmark: {str(e)}")
            raise

    def get_asset_class_benchmark(self, asset_class, lookback_days=90):
        """
        Get benchmark metrics for an asset class

        Args:
            asset_class: Asset class (e.g., 'AUTO_LOAN', 'CREDIT_CARD')
            lookback_days: Number of days to look back

        Returns:
            Asset class benchmark metrics
        """
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=lookback_days)).isoformat()

            # Scan for asset class (in production, use GSI)
            response = self.filings_table.scan(
                FilterExpression=Attr('asset_class').eq(asset_class) &
                               Attr('filing_date').gte(cutoff_date)
            )

            filings = response.get('Items', [])

            if not filings:
                return {
                    'error': 'No data found for asset class',
                    'asset_class': asset_class
                }

            # Calculate benchmarks
            benchmark = self._calculate_benchmarks(filings)
            benchmark['asset_class'] = asset_class
            benchmark['data_points'] = len(filings)
            benchmark['lookback_days'] = lookback_days

            return benchmark

        except Exception as e:
            logger.error(f"Error getting asset class benchmark: {str(e)}")
            raise

    def _calculate_benchmarks(self, filings):
        """
        Calculate benchmark statistics from filings

        Args:
            filings: List of filing dictionaries

        Returns:
            Benchmark statistics dictionary
        """
        import statistics

        # Extract metrics
        delinq_30 = [f['delinquency_30_days'] for f in filings if f.get('delinquency_30_days')]
        delinq_60 = [f['delinquency_60_days'] for f in filings if f.get('delinquency_60_days')]
        delinq_90 = [f['delinquency_90_plus_days'] for f in filings if f.get('delinquency_90_plus_days')]
        default_rates = [f['cumulative_default_rate'] for f in filings if f.get('cumulative_default_rate')]
        loss_rates = [f['cumulative_loss_rate'] for f in filings if f.get('cumulative_loss_rate')]
        fico_scores = [f['weighted_average_fico'] for f in filings if f.get('weighted_average_fico')]
        ltv_ratios = [f['weighted_average_ltv'] for f in filings if f.get('weighted_average_ltv')]

        return {
            'delinquency_metrics': {
                '30_days': {
                    'mean': statistics.mean(delinq_30) if delinq_30 else None,
                    'median': statistics.median(delinq_30) if delinq_30 else None,
                    'p25': statistics.quantiles(delinq_30, n=4)[0] if len(delinq_30) > 1 else None,
                    'p75': statistics.quantiles(delinq_30, n=4)[2] if len(delinq_30) > 1 else None
                },
                '60_days': {
                    'mean': statistics.mean(delinq_60) if delinq_60 else None,
                    'median': statistics.median(delinq_60) if delinq_60 else None
                },
                '90_plus_days': {
                    'mean': statistics.mean(delinq_90) if delinq_90 else None,
                    'median': statistics.median(delinq_90) if delinq_90 else None
                }
            },
            'loss_metrics': {
                'default_rate': {
                    'mean': statistics.mean(default_rates) if default_rates else None,
                    'median': statistics.median(default_rates) if default_rates else None
                },
                'loss_rate': {
                    'mean': statistics.mean(loss_rates) if loss_rates else None,
                    'median': statistics.median(loss_rates) if loss_rates else None
                }
            },
            'credit_quality': {
                'fico_score': {
                    'mean': statistics.mean(fico_scores) if fico_scores else None,
                    'median': statistics.median(fico_scores) if fico_scores else None
                },
                'ltv_ratio': {
                    'mean': statistics.mean(ltv_ratios) if ltv_ratios else None,
                    'median': statistics.median(ltv_ratios) if ltv_ratios else None
                }
            }
        }

    def compare_issuers(self, cik_list):
        """
        Compare multiple issuers

        Args:
            cik_list: List of CIK numbers

        Returns:
            Comparison dictionary
        """
        comparison = {}

        for cik in cik_list:
            benchmark = self.get_issuer_benchmark(cik)
            comparison[cik] = benchmark

        return comparison

    def get_risk_scores(self, cik=None, asset_class=None, risk_level=None):
        """
        Query risk scores with filters

        Args:
            cik: Filter by CIK (optional)
            asset_class: Filter by asset class (optional)
            risk_level: Filter by risk level (optional)

        Returns:
            List of risk scores
        """
        try:
            if cik:
                # Query by CIK
                response = self.risk_table.query(
                    IndexName='cik-scored_at-index',
                    KeyConditionExpression=Key('cik').eq(cik)
                )
            elif asset_class:
                # Scan by asset class
                response = self.risk_table.scan(
                    FilterExpression=Attr('asset_class').eq(asset_class)
                )
            else:
                # Get recent scores
                response = self.risk_table.scan(
                    Limit=100
                )

            scores = response.get('Items', [])

            # Filter by risk level if specified
            if risk_level:
                scores = [s for s in scores if s.get('risk_level') == risk_level]

            # Sort by scored_at descending
            scores.sort(key=lambda x: x.get('scored_at', ''), reverse=True)

            return scores

        except Exception as e:
            logger.error(f"Error getting risk scores: {str(e)}")
            raise

    def get_trending_metrics(self, asset_class=None, days=30):
        """
        Get trending metrics over time

        Args:
            asset_class: Asset class filter (optional)
            days: Number of days for trend analysis

        Returns:
            Trending metrics
        """
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            # Query filings
            filter_expr = Attr('filing_date').gte(cutoff_date)
            if asset_class:
                filter_expr = filter_expr & Attr('asset_class').eq(asset_class)

            response = self.filings_table.scan(FilterExpression=filter_expr)
            filings = response.get('Items', [])

            # Group by date and calculate daily metrics
            daily_metrics = {}
            for filing in filings:
                date = filing.get('filing_date', '')[:10]  # Get date part only

                if date not in daily_metrics:
                    daily_metrics[date] = {
                        'delinq_90': [],
                        'default_rate': [],
                        'fico': []
                    }

                if filing.get('delinquency_90_plus_days'):
                    daily_metrics[date]['delinq_90'].append(float(filing['delinquency_90_plus_days']))
                if filing.get('cumulative_default_rate'):
                    daily_metrics[date]['default_rate'].append(float(filing['cumulative_default_rate']))
                if filing.get('weighted_average_fico'):
                    daily_metrics[date]['fico'].append(float(filing['weighted_average_fico']))

            # Calculate averages
            trends = []
            for date in sorted(daily_metrics.keys()):
                metrics = daily_metrics[date]
                trends.append({
                    'date': date,
                    'avg_delinq_90': sum(metrics['delinq_90']) / len(metrics['delinq_90']) if metrics['delinq_90'] else None,
                    'avg_default_rate': sum(metrics['default_rate']) / len(metrics['default_rate']) if metrics['default_rate'] else None,
                    'avg_fico': sum(metrics['fico']) / len(metrics['fico']) if metrics['fico'] else None,
                    'count': len(filings)
                })

            return {
                'asset_class': asset_class,
                'days': days,
                'trends': trends
            }

        except Exception as e:
            logger.error(f"Error getting trending metrics: {str(e)}")
            raise


def lambda_handler(event, context):
    """
    API Gateway Lambda handler

    Routes:
        GET /benchmark/issuer/{cik}
        GET /benchmark/asset-class/{asset_class}
        GET /benchmark/compare?ciks=cik1,cik2,cik3
        GET /risk-scores?cik={cik}&asset_class={asset_class}&risk_level={level}
        GET /trending?asset_class={asset_class}&days={days}
    """
    logger.info(f"Received event: {json.dumps(event)}")

    api = BenchmarkAPI()

    try:
        # Parse request - support both API Gateway v1 and v2
        # v2 format (HTTP API)
        if 'requestContext' in event and 'http' in event['requestContext']:
            http_method = event['requestContext']['http']['method']
            path = event.get('rawPath', '/')
            # Remove stage prefix if present (e.g., /dev/path -> /path)
            stage = event['requestContext'].get('stage', '')
            if stage and path.startswith(f'/{stage}/'):
                path = path[len(stage)+1:]
            elif stage and path == f'/{stage}':
                path = '/'
            path_parameters = event.get('pathParameters', {}) or {}
            query_parameters = event.get('queryStringParameters', {}) or {}
        # v1 format (REST API)
        else:
            http_method = event.get('httpMethod', 'GET')
            path = event.get('path', '/')
            path_parameters = event.get('pathParameters', {}) or {}
            query_parameters = event.get('queryStringParameters', {}) or {}

        logger.info(f"Parsed request - Method: {http_method}, Path: {path}")

        # Route handling
        if path == '/' or path == '' or path == '/health':
            # Root path or health check - return API documentation
            result = {
                'message': 'ABSolution Benchmark API',
                'status': 'healthy',
                'version': '1.0',
                'endpoints': {
                    'GET /dev/health': 'Health check',
                    'GET /dev/benchmark/issuer/{cik}': 'Get benchmark metrics for an issuer',
                    'GET /dev/benchmark/asset-class/{asset_class}': 'Get benchmark metrics for an asset class',
                    'GET /dev/benchmark/compare?ciks=cik1,cik2': 'Compare multiple issuers',
                    'GET /dev/risk-scores?cik={cik}': 'Get risk scores with filters',
                    'GET /dev/trending?asset_class={class}&days={days}': 'Get trending metrics'
                },
                'timestamp': datetime.utcnow().isoformat()
            }

        elif path.startswith('/benchmark/issuer/'):
            cik = path_parameters.get('cik')
            lookback_days = int(query_parameters.get('lookback_days', 90))
            result = api.get_issuer_benchmark(cik, lookback_days)

        elif path.startswith('/benchmark/asset-class/'):
            asset_class = path_parameters.get('asset_class')
            lookback_days = int(query_parameters.get('lookback_days', 90))
            result = api.get_asset_class_benchmark(asset_class, lookback_days)

        elif path.startswith('/benchmark/compare'):
            ciks = query_parameters.get('ciks', '').split(',')
            result = api.compare_issuers(ciks)

        elif path.startswith('/risk-scores'):
            result = api.get_risk_scores(
                cik=query_parameters.get('cik'),
                asset_class=query_parameters.get('asset_class'),
                risk_level=query_parameters.get('risk_level')
            )

        elif path.startswith('/trending'):
            asset_class = query_parameters.get('asset_class')
            days = int(query_parameters.get('days', 30))
            result = api.get_trending_metrics(asset_class, days)

        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Endpoint not found'})
            }

        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
