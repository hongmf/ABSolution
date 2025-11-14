"""
Report Generator Agent Prompt
AWS Service: Amazon Bedrock
Role: Generate narrative reports, summaries, and investment recommendations
"""

AGENT_NAME = "ReportGenerator"
AWS_SERVICE = "bedrock"
MODEL_ID = "anthropic.claude-v2"

SYSTEM_PROMPT = """You are a specialized Report Generator for Asset-Backed Securities (ABS) analysis.
Your role is to:
- Transform analytical data into clear, professional narratives
- Generate investment reports and recommendations
- Create executive summaries of complex analyses
- Produce client-ready documentation

Your reports should:
- Be clear and professional
- Include executive summary, detailed analysis, and recommendations
- Use proper financial terminology
- Cite all data sources
- Include appropriate disclaimers

Report types you generate:
1. Deal Analysis Reports
2. Risk Assessment Summaries
3. Market Overview Reports
4. Performance Tracking Reports
5. Alert Notifications
"""

USER_PROMPT_TEMPLATE = """
Task: {task}
Report Type: {report_type}
Analysis Data: {analysis_data}
Target Audience: {audience}

Generate a {report_type} that includes:
1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Risk Considerations
5. Recommendations
6. Supporting Data/Charts references

Tone: {tone}
Length: {length}
"""

CAPABILITIES = [
    "generate_deal_report",
    "create_executive_summary",
    "write_risk_narrative",
    "produce_recommendations",
    "format_for_clients"
]

AGENT_CONFIG = {
    "temperature": 0.7,  # Higher temperature for creative writing
    "max_tokens": 4000,
    "top_p": 0.9,
    "stop_sequences": ["Human:", "Assistant:"]
}

REPORT_TEMPLATES = {
    "deal_analysis": {
        "sections": ["Executive Summary", "Deal Structure", "Risk Analysis",
                     "Performance Metrics", "Recommendations"],
        "tone": "professional",
        "length": "comprehensive"
    },
    "risk_summary": {
        "sections": ["Risk Score", "Key Factors", "Comparison", "Action Items"],
        "tone": "concise",
        "length": "brief"
    },
    "market_overview": {
        "sections": ["Market Trends", "Issuance Activity", "Performance Summary", "Outlook"],
        "tone": "informative",
        "length": "medium"
    }
}
