"""
Alert Monitor Agent Prompt
AWS Service: Amazon Bedrock + EventBridge + SNS
Role: Monitor events, detect anomalies, generate alerts
"""

AGENT_NAME = "AlertMonitor"
AWS_SERVICE = "bedrock"
MODEL_ID = "anthropic.claude-v2"

SYSTEM_PROMPT = """You are a specialized Alert Monitor for Asset-Backed Securities (ABS).
Your role is to:
- Monitor real-time events and data feeds
- Detect anomalies and significant changes
- Generate timely alerts and notifications
- Prioritize alerts by severity and urgency

You monitor:
- Performance metric deviations
- Rating changes
- Significant filings or news
- Risk threshold breaches
- Market events affecting ABS

When generating alerts:
1. Assess severity (Critical, High, Medium, Low)
2. Provide clear, actionable information
3. Include context and potential impact
4. Suggest immediate actions
5. Reference relevant historical precedents
"""

USER_PROMPT_TEMPLATE = """
Task: {task}
Event Type: {event_type}
Security: {security_id}
Event Data: {event_data}
Baseline/Threshold: {baseline}

Analyze this event and provide:
1. Alert Severity Level (Critical/High/Medium/Low)
2. Description of what changed
3. Why this matters (context and implications)
4. Recommended actions
5. Related securities that may be affected
6. Urgency (Immediate/Within 24h/Within week/FYI)
"""

CAPABILITIES = [
    "detect_anomalies",
    "assess_severity",
    "generate_alerts",
    "recommend_actions",
    "identify_patterns"
]

AGENT_CONFIG = {
    "temperature": 0.1,  # Very low temperature for alert generation
    "max_tokens": 1500,
    "top_p": 0.85,
    "stop_sequences": ["Human:", "Assistant:"]
}

ALERT_TYPES = {
    "performance": {
        "triggers": ["default_spike", "prepayment_surge", "loss_increase"],
        "severity_rules": "threshold_based"
    },
    "rating": {
        "triggers": ["downgrade", "upgrade", "watch_list"],
        "severity_rules": "magnitude_based"
    },
    "filing": {
        "triggers": ["new_8k", "amended_prospectus", "trustee_report"],
        "severity_rules": "content_based"
    },
    "market": {
        "triggers": ["spread_widening", "liquidity_issue", "sector_stress"],
        "severity_rules": "impact_based"
    }
}

SEVERITY_CRITERIA = {
    "critical": "Immediate action required, significant portfolio impact",
    "high": "Attention needed within hours, material impact",
    "medium": "Review within 24 hours, moderate impact",
    "low": "Informational, minimal immediate impact"
}
