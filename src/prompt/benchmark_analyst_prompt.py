"""
Benchmark Analyst Agent Prompt
AWS Service: Amazon Bedrock + Athena
Role: Compare performance, analyze trends, provide comparative insights
"""

AGENT_NAME = "BenchmarkAnalyst"
AWS_SERVICE = "bedrock"
MODEL_ID = "anthropic.claude-v2"

SYSTEM_PROMPT = """You are a specialized Benchmark Analyst for Asset-Backed Securities (ABS).
Your role is to:
- Compare ABS performance against benchmarks and peer groups
- Identify relative strengths and weaknesses
- Analyze market trends and positioning
- Provide competitive intelligence

You analyze:
- Performance metrics vs. indices
- Deal structures vs. market standards
- Pricing vs. comparable securities
- Historical trends and seasonality

When providing benchmark analysis:
1. Use appropriate peer groups
2. Normalize for structural differences
3. Highlight statistical significance
4. Provide context for outliers
5. Identify market opportunities
"""

USER_PROMPT_TEMPLATE = """
Task: {task}
Security/Portfolio: {security_id}
Benchmark/Peer Group: {benchmark}
Time Period: {time_period}
Metrics: {metrics}

Please provide:
1. Comparative performance analysis
2. Ranking within peer group
3. Key differentiators
4. Trend analysis
5. Market positioning insights
6. Investment implications
"""

CAPABILITIES = [
    "compare_to_benchmark",
    "peer_group_analysis",
    "trend_identification",
    "performance_attribution",
    "market_positioning"
]

AGENT_CONFIG = {
    "temperature": 0.4,  # Moderate temperature for analytical work
    "max_tokens": 2500,
    "top_p": 0.9,
    "stop_sequences": ["Human:", "Assistant:"]
}

BENCHMARK_TYPES = {
    "index": ["ABX.HE", "CMBX", "Custom ABS Indices"],
    "peer_group": ["same_asset_class", "same_vintage", "same_rating"],
    "historical": ["self_comparison", "market_average"]
}

METRICS = [
    "yield_spread",
    "default_rate",
    "prepayment_speed",
    "loss_severity",
    "credit_enhancement",
    "duration"
]
