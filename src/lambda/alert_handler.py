"""
EventBridge Alert Handler
Handles high-risk alerts and sends notifications
"""

import json
import boto3
import os
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
sns_client = boto3.client('sns')
ses_client = boto3.client('ses')
dynamodb = boto3.resource('dynamodb')

# Environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
ALERT_TABLE = os.environ.get('ALERT_TABLE', 'abs-alerts')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', 'alerts@example.com')


class AlertHandler:
    """Handles risk threshold breach alerts"""

    def __init__(self):
        self.table = dynamodb.Table(ALERT_TABLE) if ALERT_TABLE else None

    def process_high_risk_alert(self, event_detail):
        """
        Process high risk alert from EventBridge

        Args:
            event_detail: Event detail from EventBridge
        """
        try:
            filing_id = event_detail.get('filing_id')
            company_name = event_detail.get('company_name')
            asset_class = event_detail.get('asset_class')
            risk_score = event_detail.get('risk_score')
            risk_level = event_detail.get('risk_level')
            risk_factors = event_detail.get('risk_factors', [])

            logger.info(f"Processing high risk alert for {company_name} (Score: {risk_score})")

            # Create alert record
            alert_id = f"{filing_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            alert_record = {
                'alert_id': alert_id,
                'filing_id': filing_id,
                'company_name': company_name,
                'asset_class': asset_class,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'alert_time': event_detail.get('alert_time'),
                'status': 'NEW',
                'created_at': datetime.utcnow().isoformat()
            }

            # Save alert to DynamoDB
            if self.table:
                self.table.put_item(Item=alert_record)
                logger.info(f"Alert saved: {alert_id}")

            # Send notifications
            self.send_sns_notification(alert_record)
            self.send_email_notification(alert_record)

            return alert_record

        except Exception as e:
            logger.error(f"Error processing alert: {str(e)}")
            raise

    def send_sns_notification(self, alert_record):
        """Send SNS notification"""
        if not SNS_TOPIC_ARN:
            logger.warning("SNS topic not configured")
            return

        try:
            message = self._format_alert_message(alert_record)

            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"🚨 High Risk Alert: {alert_record['company_name']}",
                Message=message
            )

            logger.info("SNS notification sent")

        except Exception as e:
            logger.error(f"Error sending SNS notification: {str(e)}")

    def send_email_notification(self, alert_record):
        """Send email notification via SES"""
        try:
            html_body = self._format_alert_email(alert_record)
            text_body = self._format_alert_message(alert_record)

            ses_client.send_email(
                Source=ALERT_EMAIL,
                Destination={
                    'ToAddresses': [ALERT_EMAIL]
                },
                Message={
                    'Subject': {
                        'Data': f"High Risk Alert: {alert_record['company_name']}"
                    },
                    'Body': {
                        'Text': {
                            'Data': text_body
                        },
                        'Html': {
                            'Data': html_body
                        }
                    }
                }
            )

            logger.info("Email notification sent")

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")

    def _format_alert_message(self, alert_record):
        """Format alert as text message"""
        message = f"""
HIGH RISK ALERT
==============

Company: {alert_record['company_name']}
Asset Class: {alert_record['asset_class']}
Risk Level: {alert_record['risk_level']}
Risk Score: {alert_record['risk_score']:.4f}

Risk Factors:
"""
        for factor in alert_record.get('risk_factors', []):
            message += f"  - {factor}\n"

        message += f"""
Alert Time: {alert_record['alert_time']}
Filing ID: {alert_record['filing_id']}

Action Required: Review this issuer's performance metrics and assess potential impact.
"""
        return message

    def _format_alert_email(self, alert_record):
        """Format alert as HTML email"""
        risk_factors_html = "".join([
            f"<li>{factor}</li>" for factor in alert_record.get('risk_factors', [])
        ])

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert-box {{
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            padding: 20px;
            margin: 20px 0;
        }}
        .risk-level {{
            color: #f44336;
            font-weight: bold;
            font-size: 18px;
        }}
        .metric {{
            margin: 10px 0;
        }}
        .metric-label {{
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="alert-box">
        <h2>🚨 High Risk Alert</h2>

        <div class="metric">
            <span class="metric-label">Company:</span> {alert_record['company_name']}
        </div>

        <div class="metric">
            <span class="metric-label">Asset Class:</span> {alert_record['asset_class']}
        </div>

        <div class="metric">
            <span class="metric-label">Risk Level:</span>
            <span class="risk-level">{alert_record['risk_level']}</span>
        </div>

        <div class="metric">
            <span class="metric-label">Risk Score:</span> {alert_record['risk_score']:.4f}
        </div>

        <div class="metric">
            <span class="metric-label">Risk Factors:</span>
            <ul>
                {risk_factors_html}
            </ul>
        </div>

        <div class="metric">
            <span class="metric-label">Alert Time:</span> {alert_record['alert_time']}
        </div>

        <div class="metric">
            <span class="metric-label">Filing ID:</span> {alert_record['filing_id']}
        </div>

        <p><strong>Action Required:</strong> Review this issuer's performance metrics and assess potential impact.</p>
    </div>
</body>
</html>
"""
        return html


def lambda_handler(event, context):
    """
    Lambda handler for EventBridge events

    Event structure:
    {
        "source": "abs.risk.scorer",
        "detail-type": "High Risk Alert",
        "detail": {
            "filing_id": "...",
            "company_name": "...",
            "risk_score": 0.85,
            ...
        }
    }
    """
    logger.info(f"Received event: {json.dumps(event)}")

    handler = AlertHandler()

    try:
        # Process each record (EventBridge can batch events)
        if 'detail' in event:
            # Single event
            alert = handler.process_high_risk_alert(event['detail'])
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Alert processed',
                    'alert_id': alert['alert_id']
                })
            }
        else:
            # Batch of events
            alerts = []
            for record in event.get('Records', []):
                detail = json.loads(record.get('body', '{}'))
                alert = handler.process_high_risk_alert(detail)
                alerts.append(alert['alert_id'])

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Processed {len(alerts)} alerts',
                    'alert_ids': alerts
                })
            }

    except Exception as e:
        logger.error(f"Error in alert handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
