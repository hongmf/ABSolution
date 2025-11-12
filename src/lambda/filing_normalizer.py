"""
AWS Lambda Function: SEC Filing Normalizer
Triggered automatically when new filings arrive in S3
Normalizes filing data and stores in processed bucket
"""

import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

# Environment variables
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET', 'abs-solution-processed-data')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'abs-filings')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')


class FilingNormalizer:
    """Normalizes SEC ABS filings"""

    def __init__(self):
        self.table = dynamodb.Table(DYNAMODB_TABLE) if DYNAMODB_TABLE else None

    def normalize_filing(self, filing_data):
        """
        Normalize filing data into standardized schema
        """
        try:
            normalized = {
                'filing_id': filing_data.get('accessionNo', '').replace('-', ''),
                'accession_number': filing_data.get('accessionNo'),
                'cik': filing_data.get('cik'),
                'company_name': filing_data.get('companyName'),
                'form_type': filing_data.get('formType'),
                'filing_date': filing_data.get('filedAt'),
                'fiscal_year': filing_data.get('fiscalYear'),
                'fiscal_period': filing_data.get('fiscalPeriod'),

                # ABS-specific fields
                'asset_class': self._determine_asset_class(filing_data),
                'deal_name': filing_data.get('deal', {}).get('name'),
                'issuer_name': filing_data.get('issuer', {}).get('name'),

                # Financial metrics
                'original_pool_balance': self._safe_decimal(
                    filing_data.get('poolStats', {}).get('originalBalance')
                ),
                'current_pool_balance': self._safe_decimal(
                    filing_data.get('poolStats', {}).get('currentBalance')
                ),
                'total_principal_received': self._safe_decimal(
                    filing_data.get('poolStats', {}).get('principalReceived')
                ),

                # Performance metrics
                'delinquency_30_days': self._safe_decimal(
                    filing_data.get('performance', {}).get('delinquency30')
                ),
                'delinquency_60_days': self._safe_decimal(
                    filing_data.get('performance', {}).get('delinquency60')
                ),
                'delinquency_90_plus_days': self._safe_decimal(
                    filing_data.get('performance', {}).get('delinquency90Plus')
                ),
                'cumulative_default_rate': self._safe_decimal(
                    filing_data.get('performance', {}).get('cumulativeDefaultRate')
                ),
                'cumulative_loss_rate': self._safe_decimal(
                    filing_data.get('performance', {}).get('cumulativeLossRate')
                ),

                # Credit metrics
                'weighted_average_fico': self._safe_int(
                    filing_data.get('creditMetrics', {}).get('avgFICO')
                ),
                'weighted_average_ltv': self._safe_decimal(
                    filing_data.get('creditMetrics', {}).get('avgLTV')
                ),
                'weighted_average_dti': self._safe_decimal(
                    filing_data.get('creditMetrics', {}).get('avgDTI')
                ),

                # Metadata
                'processed_at': datetime.utcnow().isoformat(),
                'data_quality_score': self._calculate_quality_score(filing_data)
            }

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing filing: {str(e)}")
            raise

    def _determine_asset_class(self, filing_data):
        """Determine asset class from filing description"""
        description = (filing_data.get('description', '') or '').lower()

        if 'auto' in description or 'vehicle' in description:
            return 'AUTO_LOAN'
        elif 'credit card' in description or 'creditcard' in description:
            return 'CREDIT_CARD'
        elif 'student' in description or 'education' in description:
            return 'STUDENT_LOAN'
        elif 'mortgage' in description or 'residential' in description:
            return 'MORTGAGE'
        elif 'equipment' in description:
            return 'EQUIPMENT'
        elif 'commercial' in description:
            return 'COMMERCIAL'
        else:
            return 'OTHER'

    def _safe_decimal(self, value):
        """Safely convert value to Decimal"""
        if value is None:
            return None
        try:
            return float(Decimal(str(value)))
        except:
            return None

    def _safe_int(self, value):
        """Safely convert value to integer"""
        if value is None:
            return None
        try:
            return int(value)
        except:
            return None

    def _calculate_quality_score(self, filing_data):
        """Calculate data quality score based on completeness"""
        score = 0
        max_score = 10

        # Check for critical fields
        if filing_data.get('accessionNo'):
            score += 1
        if filing_data.get('cik'):
            score += 1
        if filing_data.get('filedAt'):
            score += 1

        # Check for financial metrics
        if filing_data.get('poolStats', {}).get('currentBalance'):
            score += 2

        # Check for performance metrics
        if filing_data.get('performance', {}).get('delinquency90Plus') is not None:
            score += 2

        # Check for credit metrics
        if filing_data.get('creditMetrics', {}).get('avgFICO'):
            score += 2

        # Check for deal information
        if filing_data.get('deal', {}).get('name'):
            score += 1

        return round(score / max_score, 2)

    def save_to_dynamodb(self, normalized_data):
        """Save normalized data to DynamoDB"""
        if not self.table:
            logger.warning("DynamoDB table not configured")
            return

        try:
            # Convert floats to Decimal for DynamoDB
            item = json.loads(
                json.dumps(normalized_data),
                parse_float=Decimal
            )

            self.table.put_item(Item=item)
            logger.info(f"Saved filing {normalized_data['filing_id']} to DynamoDB")

        except Exception as e:
            logger.error(f"Error saving to DynamoDB: {str(e)}")
            raise

    def save_to_s3(self, normalized_data, filing_id):
        """Save normalized data to S3"""
        try:
            key = f"normalized/{datetime.utcnow().year}/{normalized_data['asset_class']}/{filing_id}.json"

            s3_client.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=key,
                Body=json.dumps(normalized_data, indent=2),
                ContentType='application/json'
            )

            logger.info(f"Saved normalized filing to s3://{PROCESSED_BUCKET}/{key}")
            return key

        except Exception as e:
            logger.error(f"Error saving to S3: {str(e)}")
            raise


def lambda_handler(event, context):
    """
    Lambda handler triggered by S3 events or Kinesis stream
    """
    logger.info(f"Received event: {json.dumps(event)}")

    normalizer = FilingNormalizer()
    processed_count = 0
    errors = []

    try:
        # Handle S3 event
        if 'Records' in event and event['Records'][0].get('s3'):
            for record in event['Records']:
                try:
                    bucket = record['s3']['bucket']['name']
                    key = record['s3']['object']['key']

                    logger.info(f"Processing file: s3://{bucket}/{key}")

                    # Get file from S3
                    response = s3_client.get_object(Bucket=bucket, Key=key)
                    filing_data = json.loads(response['Body'].read().decode('utf-8'))

                    # Normalize
                    normalized = normalizer.normalize_filing(filing_data)

                    # Save to DynamoDB
                    normalizer.save_to_dynamodb(normalized)

                    # Save to S3
                    normalizer.save_to_s3(normalized, normalized['filing_id'])

                    processed_count += 1

                except Exception as e:
                    error_msg = f"Error processing {key}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        # Handle Kinesis event
        elif 'Records' in event and event['Records'][0].get('kinesis'):
            for record in event['Records']:
                try:
                    # Decode Kinesis data
                    payload = json.loads(
                        boto3.client('kinesis').get_records(
                            ShardIterator=record['kinesis']['sequenceNumber']
                        )['Records'][0]['Data']
                    )

                    # Normalize
                    normalized = normalizer.normalize_filing(payload)

                    # Save to DynamoDB
                    normalizer.save_to_dynamodb(normalized)

                    # Save to S3
                    normalizer.save_to_s3(normalized, normalized['filing_id'])

                    processed_count += 1

                except Exception as e:
                    error_msg = f"Error processing Kinesis record: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {processed_count} filings',
                'errors': errors if errors else None
            })
        }

    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
