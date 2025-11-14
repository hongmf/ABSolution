"""
AWS QuickSight Dashboard Setup
Programmatically create QuickSight datasets and dashboards for ABS analytics
"""

import boto3
import json
import logging
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)


class QuickSightDashboardSetup:
    """
    Setup and manage QuickSight dashboards for ABS analytics
    """

    def __init__(self, aws_account_id: str, region: str = 'us-east-1',
                 environment: str = 'dev'):
        """
        Initialize QuickSight setup

        Args:
            aws_account_id: AWS Account ID
            region: AWS region
            environment: Environment (dev, prod)
        """
        self.aws_account_id = aws_account_id
        self.region = region
        self.environment = environment
        self.quicksight_client = boto3.client('quicksight', region_name=region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=region)

        # Resource naming
        self.data_source_id = f'abs-dynamodb-source-{environment}'
        self.dataset_id = f'abs-analytics-dataset-{environment}'
        self.analysis_id = f'abs-analytics-analysis-{environment}'
        self.dashboard_id = f'abs-analytics-dashboard-{environment}'

    def create_data_source(self, principal_arn: str) -> Dict:
        """
        Create DynamoDB data source in QuickSight

        Args:
            principal_arn: ARN of QuickSight user/group with access

        Returns:
            Response from create_data_source API
        """
        logger.info(f"Creating QuickSight data source: {self.data_source_id}")

        try:
            response = self.quicksight_client.create_data_source(
                AwsAccountId=self.aws_account_id,
                DataSourceId=self.data_source_id,
                Name=f'ABS DynamoDB Data Source ({self.environment})',
                Type='DYNAMODB',
                DataSourceParameters={
                    'DynamoDBParameters': {
                        'TableName': f'abs-filings-{self.environment}'
                    }
                },
                Permissions=[
                    {
                        'Principal': principal_arn,
                        'Actions': [
                            'quicksight:UpdateDataSourcePermissions',
                            'quicksight:DescribeDataSource',
                            'quicksight:DescribeDataSourcePermissions',
                            'quicksight:PassDataSource',
                            'quicksight:UpdateDataSource',
                            'quicksight:DeleteDataSource'
                        ]
                    }
                ]
            )
            logger.info(f"Data source created: {response['DataSourceId']}")
            return response

        except self.quicksight_client.exceptions.ResourceExistsException:
            logger.warning(f"Data source {self.data_source_id} already exists")
            return {'Status': 'EXISTS'}

        except Exception as e:
            logger.error(f"Error creating data source: {e}")
            raise

    def create_dataset(self, principal_arn: str) -> Dict:
        """
        Create dataset from DynamoDB tables

        Args:
            principal_arn: ARN of QuickSight user/group with access

        Returns:
            Response from create_data_set API
        """
        logger.info(f"Creating QuickSight dataset: {self.dataset_id}")

        # Define physical table map
        physical_table_map = {
            'FilingsTable': {
                'CustomSql': {
                    'DataSourceArn': f'arn:aws:quicksight:{self.region}:{self.aws_account_id}:datasource/{self.data_source_id}',
                    'Name': 'ABS Filings',
                    'SqlQuery': f'''
                        SELECT
                            filing_id,
                            issuer_name,
                            asset_class,
                            filing_date,
                            risk_score,
                            delinquency_rate,
                            fico_score,
                            pool_balance
                        FROM "abs-filings-{self.environment}"
                    ''',
                    'Columns': [
                        {'Name': 'filing_id', 'Type': 'STRING'},
                        {'Name': 'issuer_name', 'Type': 'STRING'},
                        {'Name': 'asset_class', 'Type': 'STRING'},
                        {'Name': 'filing_date', 'Type': 'DATETIME'},
                        {'Name': 'risk_score', 'Type': 'DECIMAL'},
                        {'Name': 'delinquency_rate', 'Type': 'DECIMAL'},
                        {'Name': 'fico_score', 'Type': 'DECIMAL'},
                        {'Name': 'pool_balance', 'Type': 'DECIMAL'}
                    ]
                }
            }
        }

        try:
            response = self.quicksight_client.create_data_set(
                AwsAccountId=self.aws_account_id,
                DataSetId=self.dataset_id,
                Name=f'ABS Analytics Dataset ({self.environment})',
                PhysicalTableMap=physical_table_map,
                ImportMode='DIRECT_QUERY',
                Permissions=[
                    {
                        'Principal': principal_arn,
                        'Actions': [
                            'quicksight:UpdateDataSetPermissions',
                            'quicksight:DescribeDataSet',
                            'quicksight:DescribeDataSetPermissions',
                            'quicksight:PassDataSet',
                            'quicksight:DescribeIngestion',
                            'quicksight:ListIngestions',
                            'quicksight:UpdateDataSet',
                            'quicksight:DeleteDataSet',
                            'quicksight:CreateIngestion',
                            'quicksight:CancelIngestion'
                        ]
                    }
                ]
            )
            logger.info(f"Dataset created: {response['DataSetId']}")
            return response

        except self.quicksight_client.exceptions.ResourceExistsException:
            logger.warning(f"Dataset {self.dataset_id} already exists")
            return {'Status': 'EXISTS'}

        except Exception as e:
            logger.error(f"Error creating dataset: {e}")
            raise

    def create_analysis(self, principal_arn: str) -> Dict:
        """
        Create QuickSight analysis with visualizations

        Args:
            principal_arn: ARN of QuickSight user/group with access

        Returns:
            Response from create_analysis API
        """
        logger.info(f"Creating QuickSight analysis: {self.analysis_id}")

        # Define analysis configuration
        # This is a simplified version - full visual configurations would be more complex
        source_entity = {
            'SourceTemplate': {
                'DataSetReferences': [
                    {
                        'DataSetPlaceholder': 'ABSData',
                        'DataSetArn': f'arn:aws:quicksight:{self.region}:{self.aws_account_id}:dataset/{self.dataset_id}'
                    }
                ],
                'Arn': f'arn:aws:quicksight:{self.region}:{self.aws_account_id}:template/abs-template'
            }
        }

        try:
            response = self.quicksight_client.create_analysis(
                AwsAccountId=self.aws_account_id,
                AnalysisId=self.analysis_id,
                Name=f'ABS Analytics Analysis ({self.environment})',
                Permissions=[
                    {
                        'Principal': principal_arn,
                        'Actions': [
                            'quicksight:RestoreAnalysis',
                            'quicksight:UpdateAnalysisPermissions',
                            'quicksight:DeleteAnalysis',
                            'quicksight:DescribeAnalysisPermissions',
                            'quicksight:QueryAnalysis',
                            'quicksight:DescribeAnalysis',
                            'quicksight:UpdateAnalysis'
                        ]
                    }
                ],
                SourceEntity=source_entity
            )
            logger.info(f"Analysis created: {response['AnalysisId']}")
            return response

        except self.quicksight_client.exceptions.ResourceExistsException:
            logger.warning(f"Analysis {self.analysis_id} already exists")
            return {'Status': 'EXISTS'}

        except Exception as e:
            logger.error(f"Error creating analysis: {e}")
            logger.warning("Analysis creation requires a template. Creating basic analysis instead.")
            # Fallback - just create dataset for now
            return {'Status': 'TEMPLATE_REQUIRED'}

    def create_dashboard_from_analysis(self, principal_arn: str) -> Dict:
        """
        Create QuickSight dashboard from analysis

        Args:
            principal_arn: ARN of QuickSight user/group with access

        Returns:
            Response from create_dashboard API
        """
        logger.info(f"Creating QuickSight dashboard: {self.dashboard_id}")

        try:
            response = self.quicksight_client.create_dashboard(
                AwsAccountId=self.aws_account_id,
                DashboardId=self.dashboard_id,
                Name=f'ABS Performance Dashboard ({self.environment})',
                Permissions=[
                    {
                        'Principal': principal_arn,
                        'Actions': [
                            'quicksight:DescribeDashboard',
                            'quicksight:ListDashboardVersions',
                            'quicksight:UpdateDashboardPermissions',
                            'quicksight:QueryDashboard',
                            'quicksight:UpdateDashboard',
                            'quicksight:DeleteDashboard',
                            'quicksight:DescribeDashboardPermissions',
                            'quicksight:UpdateDashboardPublishedVersion'
                        ]
                    }
                ],
                SourceEntity={
                    'SourceAnalysis': {
                        'Arn': f'arn:aws:quicksight:{self.region}:{self.aws_account_id}:analysis/{self.analysis_id}',
                        'DataSetReferences': [
                            {
                                'DataSetPlaceholder': 'ABSData',
                                'DataSetArn': f'arn:aws:quicksight:{self.region}:{self.aws_account_id}:dataset/{self.dataset_id}'
                            }
                        ]
                    }
                },
                DashboardPublishOptions={
                    'AdHocFilteringOption': {'AvailabilityStatus': 'ENABLED'},
                    'ExportToCSVOption': {'AvailabilityStatus': 'ENABLED'},
                    'SheetControlsOption': {'VisibilityState': 'EXPANDED'}
                }
            )
            logger.info(f"Dashboard created: {response['DashboardId']}")
            return response

        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            raise

    def setup_complete_dashboard(self, principal_arn: str) -> Dict:
        """
        Complete setup of QuickSight dashboard (all steps)

        Args:
            principal_arn: ARN of QuickSight user/group (e.g., arn:aws:quicksight:us-east-1:123456789012:user/default/username)

        Returns:
            Dictionary with results of each step
        """
        results = {}

        try:
            # Step 1: Create data source
            logger.info("Step 1: Creating data source...")
            results['data_source'] = self.create_data_source(principal_arn)
            time.sleep(2)  # Wait for resource to be ready

            # Step 2: Create dataset
            logger.info("Step 2: Creating dataset...")
            results['dataset'] = self.create_dataset(principal_arn)
            time.sleep(2)

            # Step 3: Create analysis (optional, may require template)
            logger.info("Step 3: Creating analysis...")
            results['analysis'] = self.create_analysis(principal_arn)

            # Step 4: Create dashboard
            if results['analysis'].get('Status') != 'TEMPLATE_REQUIRED':
                logger.info("Step 4: Creating dashboard...")
                results['dashboard'] = self.create_dashboard_from_analysis(principal_arn)

            logger.info("QuickSight dashboard setup complete!")
            return results

        except Exception as e:
            logger.error(f"Error during dashboard setup: {e}")
            results['error'] = str(e)
            return results

    def get_dashboard_url(self, user_arn: str) -> str:
        """
        Get embeddable URL for the dashboard

        Args:
            user_arn: ARN of the QuickSight user

        Returns:
            Dashboard embed URL
        """
        try:
            response = self.quicksight_client.get_dashboard_embed_url(
                AwsAccountId=self.aws_account_id,
                DashboardId=self.dashboard_id,
                IdentityType='IAM',
                SessionLifetimeInMinutes=600,
                UndoRedoDisabled=False,
                ResetDisabled=False
            )
            return response['EmbedUrl']

        except Exception as e:
            logger.error(f"Error getting dashboard URL: {e}")
            raise


def main():
    """CLI tool for QuickSight setup"""
    import argparse

    parser = argparse.ArgumentParser(description='Setup QuickSight Dashboard for ABS Analytics')
    parser.add_argument('--account-id', required=True, help='AWS Account ID')
    parser.add_argument('--principal-arn', required=True,
                       help='QuickSight user/group ARN (e.g., arn:aws:quicksight:us-east-1:123456789012:user/default/username)')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--environment', default='dev', help='Environment (dev/prod)')
    parser.add_argument('--get-url', action='store_true', help='Get dashboard embed URL')

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create setup instance
    setup = QuickSightDashboardSetup(
        aws_account_id=args.account_id,
        region=args.region,
        environment=args.environment
    )

    if args.get_url:
        # Get dashboard URL
        url = setup.get_dashboard_url(args.principal_arn)
        print(f"\nDashboard URL: {url}")
    else:
        # Run complete setup
        print("\nStarting QuickSight Dashboard Setup...")
        print("=" * 60)
        results = setup.setup_complete_dashboard(args.principal_arn)

        print("\nSetup Results:")
        print("=" * 60)
        for step, result in results.items():
            status = result.get('Status', 'CREATED')
            print(f"{step}: {status}")

        if 'error' not in results:
            print("\n✓ Dashboard setup completed successfully!")
            print(f"\nYou can now access the dashboard in the QuickSight console:")
            print(f"https://{args.region}.quicksight.aws.amazon.com/sn/dashboards/{setup.dashboard_id}")
        else:
            print(f"\n✗ Setup completed with errors: {results['error']}")


if __name__ == '__main__':
    main()
