"""
AWS Lambda Function: ABS Risk Scorer
Automatically scores ABS issues for risk using ML models
Triggers alerts when risk thresholds are breached
"""

import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import logging
import numpy as np

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
sagemaker_runtime = boto3.client('sagemaker-runtime')
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')
sns_client = boto3.client('sns')

# Environment variables
SAGEMAKER_ENDPOINT = os.environ.get('SAGEMAKER_ENDPOINT', 'abs-risk-scoring-endpoint')
RISK_TABLE = os.environ.get('RISK_TABLE', 'abs-risk-scores')
HIGH_RISK_THRESHOLD = float(os.environ.get('HIGH_RISK_THRESHOLD', '0.75'))
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
EVENTBRIDGE_BUS = os.environ.get('EVENTBRIDGE_BUS', 'default')


class RiskScorer:
    """Calculates risk scores for ABS deals"""

    def __init__(self):
        self.table = dynamodb.Table(RISK_TABLE) if RISK_TABLE else None

    def extract_features(self, filing_data):
        """
        Extract features for risk scoring model
        """
        features = {
            # Performance metrics
            'delinquency_30_days': filing_data.get('delinquency_30_days', 0) or 0,
            'delinquency_60_days': filing_data.get('delinquency_60_days', 0) or 0,
            'delinquency_90_plus_days': filing_data.get('delinquency_90_plus_days', 0) or 0,
            'cumulative_default_rate': filing_data.get('cumulative_default_rate', 0) or 0,
            'cumulative_loss_rate': filing_data.get('cumulative_loss_rate', 0) or 0,

            # Credit quality metrics
            'weighted_average_fico': filing_data.get('weighted_average_fico', 700) or 700,
            'weighted_average_ltv': filing_data.get('weighted_average_ltv', 0) or 0,
            'weighted_average_dti': filing_data.get('weighted_average_dti', 0) or 0,

            # Pool metrics
            'pool_balance_ratio': self._calculate_pool_balance_ratio(filing_data),
            'pool_seasoning': filing_data.get('pool_seasoning_months', 0) or 0,

            # Deal structure
            'enhancement_level': filing_data.get('credit_enhancement', 0) or 0,
            'subordination_level': filing_data.get('subordination', 0) or 0,

            # Asset class encoding
            'asset_class_auto': 1 if filing_data.get('asset_class') == 'AUTO_LOAN' else 0,
            'asset_class_credit_card': 1 if filing_data.get('asset_class') == 'CREDIT_CARD' else 0,
            'asset_class_student': 1 if filing_data.get('asset_class') == 'STUDENT_LOAN' else 0,
            'asset_class_mortgage': 1 if filing_data.get('asset_class') == 'MORTGAGE' else 0,

            # Time features
            'months_since_origination': self._calculate_months_since_origination(
                filing_data.get('filing_date')
            ),
        }

        return features

    def _calculate_pool_balance_ratio(self, filing_data):
        """Calculate current balance / original balance ratio"""
        original = filing_data.get('original_pool_balance') or 0
        current = filing_data.get('current_pool_balance') or 0

        if original > 0:
            return current / original
        return 0

    def _calculate_months_since_origination(self, filing_date):
        """Calculate months since deal origination"""
        if not filing_date:
            return 0

        try:
            filing_dt = datetime.fromisoformat(filing_date.replace('Z', '+00:00'))
            months = (datetime.utcnow().year - filing_dt.year) * 12
            months += datetime.utcnow().month - filing_dt.month
            return months
        except:
            return 0

    def calculate_rule_based_score(self, features):
        """
        Calculate risk score using business rules
        (Fallback if ML model is unavailable)
        Returns score between 0 (low risk) and 1 (high risk)
        """
        risk_score = 0.0
        risk_factors = []

        # Delinquency risk
        delinq_90 = features['delinquency_90_plus_days']
        if delinq_90 > 0.10:  # 10% delinquency
            risk_score += 0.30
            risk_factors.append(f"High 90+ day delinquency: {delinq_90:.2%}")
        elif delinq_90 > 0.05:  # 5% delinquency
            risk_score += 0.15
            risk_factors.append(f"Elevated 90+ day delinquency: {delinq_90:.2%}")

        # Credit quality risk
        fico = features['weighted_average_fico']
        if fico < 620:
            risk_score += 0.25
            risk_factors.append(f"Low FICO score: {fico}")
        elif fico < 660:
            risk_score += 0.10
            risk_factors.append(f"Below average FICO score: {fico}")

        # Loss rate risk
        loss_rate = features['cumulative_loss_rate']
        if loss_rate > 0.05:  # 5% cumulative losses
            risk_score += 0.25
            risk_factors.append(f"High cumulative loss rate: {loss_rate:.2%}")
        elif loss_rate > 0.02:
            risk_score += 0.10
            risk_factors.append(f"Elevated cumulative loss rate: {loss_rate:.2%}")

        # LTV risk (for secured assets)
        ltv = features['weighted_average_ltv']
        if ltv > 0.90:  # 90% LTV
            risk_score += 0.15
            risk_factors.append(f"High LTV: {ltv:.2%}")
        elif ltv > 0.80:
            risk_score += 0.05
            risk_factors.append(f"Elevated LTV: {ltv:.2%}")

        # Balance depletion risk
        balance_ratio = features['pool_balance_ratio']
        if balance_ratio < 0.20 and features['months_since_origination'] < 24:
            risk_score += 0.10
            risk_factors.append("Rapid pool depletion")

        # Cap the score at 1.0
        risk_score = min(risk_score, 1.0)

        return {
            'risk_score': round(risk_score, 4),
            'risk_level': self._categorize_risk(risk_score),
            'risk_factors': risk_factors,
            'scoring_method': 'rule_based'
        }

    def score_with_sagemaker(self, features):
        """
        Score using SageMaker endpoint
        """
        try:
            # Prepare feature vector (order must match training)
            feature_vector = [
                features['delinquency_30_days'],
                features['delinquency_60_days'],
                features['delinquency_90_plus_days'],
                features['cumulative_default_rate'],
                features['cumulative_loss_rate'],
                features['weighted_average_fico'],
                features['weighted_average_ltv'],
                features['weighted_average_dti'],
                features['pool_balance_ratio'],
                features['pool_seasoning'],
                features['enhancement_level'],
                features['subordination_level'],
                features['asset_class_auto'],
                features['asset_class_credit_card'],
                features['asset_class_student'],
                features['asset_class_mortgage'],
                features['months_since_origination']
            ]

            # Invoke SageMaker endpoint
            response = sagemaker_runtime.invoke_endpoint(
                EndpointName=SAGEMAKER_ENDPOINT,
                ContentType='application/json',
                Body=json.dumps({'instances': [feature_vector]})
            )

            # Parse response
            result = json.loads(response['Body'].read().decode())
            risk_score = float(result['predictions'][0][0])

            logger.info(f"SageMaker risk score: {risk_score}")

            return {
                'risk_score': round(risk_score, 4),
                'risk_level': self._categorize_risk(risk_score),
                'risk_factors': self._interpret_ml_score(features, risk_score),
                'scoring_method': 'ml_model'
            }

        except Exception as e:
            logger.error(f"Error calling SageMaker endpoint: {str(e)}")
            # Fallback to rule-based scoring
            logger.info("Falling back to rule-based scoring")
            return self.calculate_rule_based_score(features)

    def _categorize_risk(self, score):
        """Categorize risk score into levels"""
        if score >= 0.75:
            return 'CRITICAL'
        elif score >= 0.60:
            return 'HIGH'
        elif score >= 0.40:
            return 'MEDIUM'
        elif score >= 0.20:
            return 'LOW'
        else:
            return 'MINIMAL'

    def _interpret_ml_score(self, features, score):
        """Provide interpretability for ML score"""
        factors = []

        # Identify key risk drivers
        if features['delinquency_90_plus_days'] > 0.05:
            factors.append(f"High delinquency: {features['delinquency_90_plus_days']:.2%}")

        if features['weighted_average_fico'] < 660:
            factors.append(f"Low FICO: {features['weighted_average_fico']}")

        if features['cumulative_loss_rate'] > 0.02:
            factors.append(f"High loss rate: {features['cumulative_loss_rate']:.2%}")

        return factors

    def save_risk_score(self, filing_id, filing_data, risk_result):
        """Save risk score to DynamoDB"""
        if not self.table:
            logger.warning("Risk table not configured")
            return

        try:
            item = {
                'filing_id': filing_id,
                'accession_number': filing_data.get('accession_number'),
                'company_name': filing_data.get('company_name'),
                'asset_class': filing_data.get('asset_class'),
                'filing_date': filing_data.get('filing_date'),
                'risk_score': Decimal(str(risk_result['risk_score'])),
                'risk_level': risk_result['risk_level'],
                'risk_factors': risk_result['risk_factors'],
                'scoring_method': risk_result['scoring_method'],
                'scored_at': datetime.utcnow().isoformat()
            }

            self.table.put_item(Item=item)
            logger.info(f"Saved risk score for {filing_id}")

        except Exception as e:
            logger.error(f"Error saving risk score: {str(e)}")

    def trigger_alert_if_needed(self, filing_data, risk_result):
        """Trigger alert via EventBridge if risk threshold breached"""
        if risk_result['risk_score'] >= HIGH_RISK_THRESHOLD:
            try:
                # Send EventBridge event
                eventbridge.put_events(
                    Entries=[{
                        'Source': 'abs.risk.scorer',
                        'DetailType': 'High Risk Alert',
                        'Detail': json.dumps({
                            'filing_id': filing_data.get('filing_id'),
                            'company_name': filing_data.get('company_name'),
                            'asset_class': filing_data.get('asset_class'),
                            'risk_score': risk_result['risk_score'],
                            'risk_level': risk_result['risk_level'],
                            'risk_factors': risk_result['risk_factors'],
                            'alert_time': datetime.utcnow().isoformat()
                        }),
                        'EventBusName': EVENTBRIDGE_BUS
                    }]
                )

                logger.info(f"High risk alert triggered for {filing_data.get('filing_id')}")

                # Also send SNS notification
                if SNS_TOPIC_ARN:
                    sns_client.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Subject=f"High Risk Alert: {filing_data.get('company_name')}",
                        Message=json.dumps(risk_result, indent=2)
                    )

            except Exception as e:
                logger.error(f"Error triggering alert: {str(e)}")


def lambda_handler(event, context):
    """
    Lambda handler for risk scoring
    Triggered by new normalized filings
    """
    logger.info(f"Received event: {json.dumps(event)}")

    scorer = RiskScorer()
    processed_count = 0
    high_risk_count = 0

    try:
        # Process each record
        for record in event.get('Records', []):
            try:
                # Extract filing data
                if 's3' in record:
                    bucket = record['s3']['bucket']['name']
                    key = record['s3']['object']['key']
                    response = s3_client.get_object(Bucket=bucket, Key=key)
                    filing_data = json.loads(response['Body'].read().decode('utf-8'))
                else:
                    filing_data = json.loads(record.get('body', '{}'))

                filing_id = filing_data.get('filing_id')
                logger.info(f"Scoring filing: {filing_id}")

                # Extract features
                features = scorer.extract_features(filing_data)

                # Calculate risk score
                risk_result = scorer.score_with_sagemaker(features)

                # Save risk score
                scorer.save_risk_score(filing_id, filing_data, risk_result)

                # Check for alerts
                scorer.trigger_alert_if_needed(filing_data, risk_result)

                if risk_result['risk_level'] in ['HIGH', 'CRITICAL']:
                    high_risk_count += 1

                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing record: {str(e)}")
                continue

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Scored {processed_count} filings',
                'high_risk_count': high_risk_count
            })
        }

    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
