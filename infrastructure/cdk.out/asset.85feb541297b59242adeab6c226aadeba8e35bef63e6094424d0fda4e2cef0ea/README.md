# Multi-Agent System

This directory contains the ABSolution Multi-Agent AI System components.

## Directory Structure

```
agents/
├── __init__.py              # Package initialization
├── agent_coordinator.py     # Main orchestration logic
└── dialogue_panel.py        # User interaction interface
```

## Quick Start

### 1. Local Testing

```python
from agents import AgentCoordinator

# Initialize coordinator
coordinator = AgentCoordinator()

# Process a query
result = coordinator.orchestrate_multi_agent(
    user_query="What's the risk score for security ABC-123?",
    session_id="test-session",
    context={"security_id": "ABC-123"}
)

print(result['final_response'])
```

### 2. API Usage

```bash
# Create session
curl -X POST https://your-api-endpoint/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'

# Send message
curl -X POST https://your-api-endpoint/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "Analyze security ABC-123"
  }'
```

## Agent Types

The system coordinates 5 specialized agents:

1. **Data Analyst** - Queries and analyzes SEC filings
2. **Risk Assessor** - Evaluates credit risk with ML models
3. **Report Generator** - Creates narrative reports
4. **Benchmark Analyst** - Performs comparative analysis
5. **Alert Monitor** - Detects anomalies and generates alerts

See `/docs/multi_agent_system.md` for detailed documentation.

## Configuration

Agents are configured via:
- Prompt files in `/src/prompt/`
- Config file at `/config/agent_config.yaml`
- Environment variables

## AWS Services Used

- Amazon Bedrock (LLM)
- SageMaker (ML models)
- DynamoDB (state)
- Lambda (compute)
- Step Functions (orchestration)

## Deployment

```bash
# Deploy infrastructure
./scripts/deploy_agents.sh

# Run tests
python scripts/test_agents.py
```

See `/docs/multi_agent_system.md` for complete deployment guide.
