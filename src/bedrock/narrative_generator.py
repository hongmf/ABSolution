"""
Amazon Bedrock Integration for AI Narrative Insights
Generates natural language insights about ABS performance trends
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
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

# Environment variables
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
FILINGS_TABLE = os.environ.get('FILINGS_TABLE', 'abs-filings')
RISK_TABLE = os.environ.get('RISK_TABLE', 'abs-risk-scores')


class NarrativeGenerator:
    """Generates AI-powered narrative insights using Amazon Bedrock"""

    def __init__(self):
        self.bedrock = bedrock_runtime
        self.model_id = BEDROCK_MODEL_ID
        self.filings_table = dynamodb.Table(FILINGS_TABLE) if FILINGS_TABLE else None
        self.risk_table = dynamodb.Table(RISK_TABLE) if RISK_TABLE else None

    def generate_issuer_narrative(self, issuer_data, risk_data=None):
        """
        Generate narrative insights for an issuer

        Args:
            issuer_data: Dictionary with issuer filing data
            risk_data: Optional risk scoring data

        Returns:
            Generated narrative text
        """
        try:
            prompt = self._build_issuer_prompt(issuer_data, risk_data)

            logger.info(f"Generating narrative for {issuer_data.get('company_name')}")

            narrative = self._invoke_bedrock(prompt)

            return {
                'issuer': issuer_data.get('company_name'),
                'narrative': narrative,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating issuer narrative: {str(e)}")
            raise

    def generate_market_narrative(self, asset_class, market_data):
        """
        Generate market-level narrative for an asset class

        Args:
            asset_class: Asset class (e.g., 'AUTO_LOAN')
            market_data: Dictionary with market benchmarks and trends

        Returns:
            Generated narrative text
        """
        try:
            prompt = self._build_market_prompt(asset_class, market_data)

            logger.info(f"Generating market narrative for {asset_class}")

            narrative = self._invoke_bedrock(prompt)

            return {
                'asset_class': asset_class,
                'narrative': narrative,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating market narrative: {str(e)}")
            raise

    def generate_comparative_narrative(self, issuers_data):
        """
        Generate comparative analysis between multiple issuers

        Args:
            issuers_data: List of issuer data dictionaries

        Returns:
            Generated comparative narrative
        """
        try:
            prompt = self._build_comparative_prompt(issuers_data)

            logger.info(f"Generating comparative narrative for {len(issuers_data)} issuers")

            narrative = self._invoke_bedrock(prompt)

            return {
                'issuers': [i.get('company_name') for i in issuers_data],
                'narrative': narrative,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating comparative narrative: {str(e)}")
            raise

    def _build_issuer_prompt(self, issuer_data, risk_data=None):
        """Build prompt for issuer analysis"""

        risk_context = ""
        if risk_data:
            risk_context = f"""
Risk Assessment:
- Risk Level: {risk_data.get('risk_level')}
- Risk Score: {risk_data.get('risk_score', 0):.2%}
- Risk Factors: {', '.join(risk_data.get('risk_factors', []))}
"""

        prompt = f"""Analyze the following Asset-Backed Securities issuer and provide insightful narrative commentary:

Issuer: {issuer_data.get('company_name')}
Asset Class: {issuer_data.get('asset_class')}
Deal Name: {issuer_data.get('deal_name')}

Performance Metrics:
- Current Pool Balance: ${issuer_data.get('current_pool_balance', 0):,.0f}
- Original Pool Balance: ${issuer_data.get('original_pool_balance', 0):,.0f}
- 30-day Delinquency Rate: {issuer_data.get('delinquency_30_days', 0):.2%}
- 60-day Delinquency Rate: {issuer_data.get('delinquency_60_days', 0):.2%}
- 90+ day Delinquency Rate: {issuer_data.get('delinquency_90_plus_days', 0):.2%}
- Cumulative Default Rate: {issuer_data.get('cumulative_default_rate', 0):.2%}
- Cumulative Loss Rate: {issuer_data.get('cumulative_loss_rate', 0):.2%}

Credit Quality:
- Weighted Average FICO: {issuer_data.get('weighted_average_fico', 0):.0f}
- Weighted Average LTV: {issuer_data.get('weighted_average_ltv', 0):.2%}
- Weighted Average DTI: {issuer_data.get('weighted_average_dti', 0):.2%}

{risk_context}

Please provide:
1. A concise summary of the issuer's performance (2-3 sentences)
2. Key trends or concerns based on the metrics
3. Comparison to typical {issuer_data.get('asset_class')} benchmarks
4. Forward-looking insights or recommendations

Keep the narrative professional, data-driven, and actionable for financial analysts."""

        return prompt

    def _build_market_prompt(self, asset_class, market_data):
        """Build prompt for market analysis"""

        prompt = f"""Analyze the current state of the {asset_class} Asset-Backed Securities market:

Market Benchmarks (Last 90 Days):

Delinquency Metrics:
- Average 30-day Delinquency: {market_data.get('avg_delinq_30', 0):.2%}
- Average 60-day Delinquency: {market_data.get('avg_delinq_60', 0):.2%}
- Average 90+ day Delinquency: {market_data.get('avg_delinq_90', 0):.2%}

Credit Quality:
- Average FICO Score: {market_data.get('avg_fico', 0):.0f}
- Average LTV Ratio: {market_data.get('avg_ltv', 0):.2%}

Loss Metrics:
- Average Default Rate: {market_data.get('avg_default_rate', 0):.2%}
- Average Loss Rate: {market_data.get('avg_loss_rate', 0):.2%}

Trends:
{json.dumps(market_data.get('trends', {}), indent=2)}

Please provide:
1. Overall market health assessment for {asset_class}
2. Notable trends (improving, deteriorating, or stable)
3. Potential risk factors on the horizon
4. Market dynamics and what's driving current performance

Keep the narrative concise, insightful, and suitable for executive briefings."""

        return prompt

    def _build_comparative_prompt(self, issuers_data):
        """Build prompt for comparative analysis"""

        issuers_summary = []
        for issuer in issuers_data:
            issuers_summary.append(f"""
{issuer.get('company_name')}:
- Asset Class: {issuer.get('asset_class')}
- 90+ Day Delinquency: {issuer.get('delinquency_90_plus_days', 0):.2%}
- Default Rate: {issuer.get('cumulative_default_rate', 0):.2%}
- Avg FICO: {issuer.get('weighted_average_fico', 0):.0f}
- Pool Balance: ${issuer.get('current_pool_balance', 0):,.0f}
""")

        prompt = f"""Compare the following ABS issuers and provide comparative insights:

{chr(10).join(issuers_summary)}

Please provide:
1. Ranking of issuers by overall credit quality
2. Key differentiators between the issuers
3. Which issuer shows the strongest/weakest performance and why
4. Risk-adjusted recommendations for investors

Be specific, quantitative where possible, and highlight meaningful differences."""

        return prompt

    def _invoke_bedrock(self, prompt, max_tokens=2000):
        """
        Invoke Amazon Bedrock to generate text

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        try:
            # Prepare request for Claude model
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "top_p": 0.9
            }

            # Invoke Bedrock
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            generated_text = response_body['content'][0]['text']

            logger.info(f"Generated {len(generated_text)} characters")

            return generated_text

        except Exception as e:
            logger.error(f"Error invoking Bedrock: {str(e)}")
            raise


def lambda_handler(event, context):
    """
    Lambda handler for narrative generation

    Event structure:
    {
        "type": "issuer" | "market" | "comparative",
        "data": {...}
    }
    """
    logger.info(f"Received event: {json.dumps(event)}")

    generator = NarrativeGenerator()

    try:
        event_type = event.get('type', 'issuer')

        if event_type == 'issuer':
            issuer_data = event.get('issuer_data', {})
            risk_data = event.get('risk_data')
            result = generator.generate_issuer_narrative(issuer_data, risk_data)

        elif event_type == 'market':
            asset_class = event.get('asset_class')
            market_data = event.get('market_data', {})
            result = generator.generate_market_narrative(asset_class, market_data)

        elif event_type == 'comparative':
            issuers_data = event.get('issuers_data', [])
            result = generator.generate_comparative_narrative(issuers_data)

        else:
            raise ValueError(f"Unknown event type: {event_type}")

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Error generating narrative: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


# Example usage
if __name__ == '__main__':
    # Example issuer data
    sample_issuer = {
        'company_name': 'Example Auto Loan Trust 2024-1',
        'asset_class': 'AUTO_LOAN',
        'deal_name': 'EALT 2024-1',
        'current_pool_balance': 500000000,
        'original_pool_balance': 750000000,
        'delinquency_30_days': 0.025,
        'delinquency_60_days': 0.015,
        'delinquency_90_plus_days': 0.008,
        'cumulative_default_rate': 0.032,
        'cumulative_loss_rate': 0.018,
        'weighted_average_fico': 720,
        'weighted_average_ltv': 0.78,
        'weighted_average_dti': 0.35
    }

    sample_risk = {
        'risk_level': 'MEDIUM',
        'risk_score': 0.45,
        'risk_factors': ['Elevated 30-day delinquency', 'Pool seasoning']
    }

    generator = NarrativeGenerator()
    result = generator.generate_issuer_narrative(sample_issuer, sample_risk)
    print(json.dumps(result, indent=2))
