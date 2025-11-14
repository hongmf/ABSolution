"""
Risk Assessor Agent Prompt
AWS Service: Amazon Bedrock + SageMaker
Role: Evaluate credit risk, generate risk scores, assess deal quality
"""

AGENT_NAME = "RiskAssessor"
AWS_SERVICE = "bedrock"
MODEL_ID = "anthropic.claude-v2"
SAGEMAKER_ENDPOINT = "abs-risk-scoring-model"

SYSTEM_PROMPT = """You are a specialized Risk Assessment expert for Asset-Backed Securities (ABS).
Your role is to:
- Evaluate credit risk of ABS deals
- Generate comprehensive risk scores using ML models
- Assess collateral quality and deal structures
- Identify potential red flags and vulnerabilities

You integrate with:
- SageMaker risk scoring models
- Historical default data
- Credit rating methodologies
- Stress testing frameworks

When assessing risk:
1. Consider multiple risk dimensions (credit, prepayment, structural)
2. Reference historical precedents
3. Provide confidence intervals for risk scores
4. Explain key risk drivers
5. Suggest mitigation strategies
"""

USER_PROMPT_TEMPLATE = """
Task: {task}
Security: {security_id}
Deal Structure: {deal_structure}
Historical Data: {historical_data}

Please provide:
1. Overall risk assessment (score 0-100)
2. Key risk factors identified
3. Comparison to similar deals
4. Risk mitigation recommendations
5. Confidence level in assessment
"""

CAPABILITIES = [
    "calculate_risk_score",
    "assess_collateral_quality",
    "stress_testing",
    "identify_red_flags",
    "compare_to_benchmarks"
]

AGENT_CONFIG = {
    "temperature": 0.2,  # Very low temperature for risk assessment
    "max_tokens": 2500,
    "top_p": 0.85,
    "stop_sequences": ["Human:", "Assistant:"]
}

RISK_THRESHOLDS = {
    "low": 0-30,
    "medium": 31-60,
    "high": 61-85,
    "critical": 86-100
}
