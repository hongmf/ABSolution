# ABSolution Multi-Agent AI System

## Overview

The ABSolution Multi-Agent AI System is an AWS-powered conversational AI platform that coordinates five specialized agents to provide comprehensive Asset-Backed Securities (ABS) analysis.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Dialogue Panel                           │
│              (API Gateway + WebSocket)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Agent Coordinator                               │
│         (Intent Classification & Routing)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
│ Data Analyst │ │Risk Assessor│ │  Report    │
│   (Bedrock)  │ │(Bedrock+SM) │ │ Generator  │
└──────────────┘ └─────────────┘ └─────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────────┐ ┌─▼──────────────┐
│Benchmark Analyst │ │ Alert Monitor  │
│    (Bedrock)     │ │ (Bedrock+EB)   │
└──────────────────┘ └────────────────┘
```

### AWS Services Used

- **Amazon Bedrock**: LLM capabilities for all agents (Claude v2)
- **Amazon SageMaker**: ML-based risk scoring model
- **AWS Lambda**: Serverless compute for agent execution
- **API Gateway**: REST API and WebSocket for dialogue panel
- **Amazon DynamoDB**: Conversation state and session management
- **AWS Step Functions**: Multi-agent orchestration workflows
- **Amazon EventBridge**: Event-driven agent triggers
- **Amazon S3**: Data lake for SEC filings
- **Amazon Athena**: Query service for structured data

## Five Specialized Agents

### 1. Data Analyst Agent
**File**: `src/prompt/data_analyst_prompt.py`

**Purpose**: Query and analyze SEC filings data, extract key financial metrics

**Capabilities**:
- Query SEC EDGAR filings from S3
- Extract metrics and deal structures
- Identify trends in ABS issuances
- Provide data-driven insights

**Use Cases**:
- "Show me all auto ABS deals from Q1 2024"
- "What are the key metrics for security XYZ?"
- "Extract collateral composition data"

### 2. Risk Assessor Agent
**File**: `src/prompt/risk_assessor_prompt.py`

**Purpose**: Evaluate credit risk, generate risk scores, assess deal quality

**Capabilities**:
- Calculate risk scores (0-100)
- Assess collateral quality
- Stress testing scenarios
- Identify red flags
- Compare to benchmarks

**Integration**: Uses SageMaker ML model for quantitative risk scoring

**Use Cases**:
- "What's the risk score for this deal?"
- "Assess the credit quality of this pool"
- "What are the main risk factors?"

### 3. Report Generator Agent
**File**: `src/prompt/report_generator_prompt.py`

**Purpose**: Generate narrative reports, summaries, and investment recommendations

**Capabilities**:
- Create deal analysis reports
- Generate executive summaries
- Write risk narratives
- Produce client-ready documentation
- Format recommendations

**Report Types**:
- Deal Analysis Reports
- Risk Assessment Summaries
- Market Overview Reports
- Performance Tracking Reports

**Use Cases**:
- "Generate a deal analysis report for security ABC"
- "Create an executive summary of today's findings"
- "Write investment recommendations"

### 4. Benchmark Analyst Agent
**File**: `src/prompt/benchmark_analyst_prompt.py`

**Purpose**: Compare performance, analyze trends, provide comparative insights

**Capabilities**:
- Compare to indices (ABX.HE, CMBX, etc.)
- Peer group analysis
- Trend identification
- Performance attribution
- Market positioning

**Use Cases**:
- "How does this deal compare to similar vintage?"
- "Compare yield spread vs. market average"
- "Show performance vs. ABX.HE index"

### 5. Alert Monitor Agent
**File**: `src/prompt/alert_monitor_prompt.py`

**Purpose**: Monitor events, detect anomalies, generate timely alerts

**Capabilities**:
- Detect anomalies in performance data
- Assess severity (Critical/High/Medium/Low)
- Generate actionable alerts
- Recommend immediate actions
- Pattern identification

**Alert Types**:
- Performance deviations (defaults, prepayments)
- Rating changes
- Significant filings
- Market events

**Use Cases**:
- "Monitor security XYZ for unusual activity"
- "Alert me if default rates spike"
- "What securities need immediate attention?"

## Agent Coordination

### Intent-Based Routing

The Agent Coordinator automatically routes queries to appropriate agents:

| User Intent | Primary Agent | Supporting Agents |
|-------------|---------------|-------------------|
| Query data | Data Analyst | - |
| Risk assessment | Risk Assessor | Data Analyst |
| Generate report | Report Generator | Data Analyst, Risk Assessor |
| Compare performance | Benchmark Analyst | Data Analyst |
| Monitor alerts | Alert Monitor | - |

### Execution Strategies

**Sequential Execution**:
```
User Query → Data Analyst → Risk Assessor → Report Generator
```

**Parallel Execution**:
```
                ┌─→ Data Analyst ──┐
User Query ─────┼─→ Risk Assessor ──┼─→ Report Generator
                └─→ Benchmark Analyst ┘
```

### Step Functions Workflow

Complex queries trigger AWS Step Functions workflows that:
1. Classify user intent
2. Route to appropriate agents
3. Execute agents (parallel where possible)
4. Aggregate results
5. Generate final response

**Workflow Definition**: `config/agent_workflow.json`

## Dialogue Panel API

### REST API Endpoints

**Base URL**: `https://api.absolution.example.com/prod`

#### Create Session
```http
POST /session
Content-Type: application/json

{
  "user_id": "optional_user_id"
}

Response:
{
  "session_id": "uuid-string"
}
```

#### Send Message
```http
POST /message
Content-Type: application/json

{
  "session_id": "uuid-string",
  "message": "What is the risk score for security ABC?",
  "attachments": []  // optional
}

Response:
{
  "message": "The risk score for security ABC is 45 (Medium risk)...",
  "metadata": {
    "agents_consulted": ["risk_assessor", "data_analyst"],
    "timestamp": "2024-01-15T10:30:00Z",
    "session_id": "uuid-string"
  },
  "suggestions": [
    "What are the main risk factors?",
    "Compare to similar deals",
    "Generate a risk report"
  ],
  "visualization_hints": [
    {
      "type": "gauge",
      "description": "Risk score gauge recommended"
    }
  ]
}
```

#### Get Conversation History
```http
GET /history/{session_id}

Response:
{
  "history": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "user": "What is the risk score?",
      "assistant": "The risk score is 45..."
    }
  ]
}
```

#### Export Conversation
```http
POST /export
Content-Type: application/json

{
  "session_id": "uuid-string",
  "format": "markdown"  // json, markdown, or text
}

Response: Formatted conversation export
```

### WebSocket API

For real-time dialogue:

```javascript
const ws = new WebSocket('wss://ws.absolution.example.com/prod');

// On connect
ws.send(JSON.stringify({
  action: 'message',
  session_id: 'uuid-string',
  message: 'What is the risk score?'
}));

// Receive response
ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log(response.message);
};
```

## Deployment

### Prerequisites
```bash
# Install AWS CDK
npm install -g aws-cdk

# Install Python dependencies
pip install -r requirements.txt

# Install CDK dependencies
cd infrastructure
pip install -r requirements.txt
```

### Deploy Infrastructure
```bash
# Bootstrap CDK (first time only)
cdk bootstrap aws://ACCOUNT-ID/REGION

# Deploy multi-agent stack
cd infrastructure
cdk deploy MultiAgentStack

# Note the API Gateway URL from outputs
```

### Configure Bedrock Access
```bash
# Enable Bedrock models in AWS Console
# Required models: anthropic.claude-v2

# Or via CLI:
aws bedrock put-model-invocation-logging-configuration \
  --logging-config '{"cloudWatchConfig":{"enabled":true}}'
```

### Deploy SageMaker Model
```bash
# Train and deploy risk scoring model
python src/sagemaker/train_risk_model.py
python src/sagemaker/inference.py --deploy
```

## Usage Examples

### Example 1: Risk Assessment
```
User: "Assess the risk for security ABC-123"

System:
1. Routes to Risk Assessor (primary)
2. Invokes Data Analyst (supporting) to fetch security data
3. Risk Assessor analyzes with ML model
4. Returns: "Risk Score: 45 (Medium). Key factors: ..."
```

### Example 2: Comprehensive Report
```
User: "Generate a deal analysis report for security ABC-123"

System:
1. Routes to Report Generator (primary)
2. Parallel execution:
   - Data Analyst: Fetch deal data
   - Risk Assessor: Calculate risk score
   - Benchmark Analyst: Compare to peers
3. Report Generator compiles comprehensive report
4. Returns: Full report with executive summary
```

### Example 3: Monitoring
```
User: "Alert me if any security shows default spike"

System:
1. Routes to Alert Monitor
2. Sets up EventBridge rule
3. Monitors data lake continuously
4. Generates alerts when conditions met
```

## Configuration

### Agent Configuration
Edit `config/agent_config.yaml` to customize:
- Model IDs and parameters
- Capabilities and thresholds
- Orchestration strategies
- Infrastructure settings

### Environment Variables
```bash
# Required
export AWS_REGION="us-east-1"
export CONVERSATION_TABLE="abs-agent-conversations"
export SESSION_TABLE="abs-agent-sessions"
export SAGEMAKER_RISK_ENDPOINT="abs-risk-scoring-model"

# Optional
export BEDROCK_MODEL_ID="anthropic.claude-v2"
export MAX_TOKENS=2000
export TEMPERATURE=0.7
```

## Monitoring & Logging

### CloudWatch Logs
- Lambda logs: `/aws/lambda/abs-agent-*`
- Step Functions logs: `/aws/stepfunctions/abs-multi-agent-workflow`
- API Gateway logs: `/aws/apigateway/dialogue-api`

### Metrics
- Agent invocation count
- Response latency
- Error rates
- Cost per query

### Bedrock Monitoring
```bash
# View Bedrock invocation logs
aws logs tail /aws/bedrock/modelinvocations --follow
```

## Cost Optimization

1. **Use appropriate models**: Claude v2 for complex analysis, Titan for simple tasks
2. **Implement caching**: Cache frequent queries in DynamoDB
3. **Parallel execution**: Run independent agents concurrently
4. **Session TTL**: Auto-expire old sessions (24 hours)
5. **DynamoDB on-demand**: Pay only for actual usage

## Security

1. **IAM Roles**: Least privilege access for all Lambda functions
2. **API Authentication**: Add API Gateway authorizers (Cognito/Lambda)
3. **Data Encryption**: DynamoDB encryption at rest, TLS in transit
4. **VPC**: Deploy Lambdas in private subnets if needed
5. **Secrets Management**: Use AWS Secrets Manager for credentials

## Troubleshooting

### Agent Not Responding
```bash
# Check Lambda logs
aws logs tail /aws/lambda/abs-agent-coordinator --follow

# Check Bedrock access
aws bedrock list-foundation-models
```

### High Latency
- Enable CloudWatch metrics
- Check Step Functions execution history
- Consider increasing Lambda memory

### DynamoDB Throttling
- Switch to provisioned capacity if needed
- Add auto-scaling policies

## Future Enhancements

1. **Multi-modal Support**: Add document/image analysis
2. **Streaming Responses**: Real-time token streaming
3. **Agent Learning**: Fine-tune models on historical queries
4. **Advanced Visualization**: Auto-generate charts from data
5. **Voice Interface**: Add Amazon Lex integration
6. **Multi-language**: Support international users

## References

- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS Step Functions Guide](https://docs.aws.amazon.com/step-functions/)
- [Agent Prompt Engineering Best Practices](https://docs.anthropic.com/claude/docs)
