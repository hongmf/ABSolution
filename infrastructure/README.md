# ABSolution Infrastructure

AWS CDK Infrastructure for the Multi-Agent AI System.

## Quick Start

### Install Dependencies

```bash
cd infrastructure
pip install -r requirements.txt
```

### Deploy

```bash
# Set AWS environment variables (if not already set)
export AWS_REGION=us-east-1

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack
cdk deploy ABSolutionMultiAgentStack
```

### Other CDK Commands

```bash
# Synthesize CloudFormation template
cdk synth

# Show differences from deployed stack
cdk diff

# Destroy the stack
cdk destroy ABSolutionMultiAgentStack

# List all stacks
cdk ls
```

## Stack Components

The `ABSolutionMultiAgentStack` creates:

### 1. DynamoDB Tables
- **abs-agent-conversations**: Stores conversation history
- **abs-agent-sessions**: Manages user sessions with TTL

### 2. Lambda Functions
- **abs-agent-coordinator**: Main orchestration function
- **abs-dialogue-rest-api**: REST API handler
- **abs-agent-data_analyst**: Data analyst agent
- **abs-agent-risk_assessor**: Risk assessor agent
- **abs-agent-report_generator**: Report generator agent
- **abs-agent-benchmark_analyst**: Benchmark analyst agent
- **abs-agent-alert_monitor**: Alert monitor agent

### 3. API Gateway
- REST API with CORS enabled
- Endpoints:
  - `POST /session` - Create session
  - `POST /message` - Send message
  - `GET /history/{session_id}` - Get history
  - `POST /export` - Export conversation

### 4. Step Functions
- Workflow for multi-agent orchestration
- Parallel and sequential execution support

### 5. EventBridge Rules
- Daily market summary (8 AM UTC)
- Alert monitoring (every 15 minutes)

## Configuration

### Environment Variables

Set these before deployment:

```bash
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION=us-east-1
```

### Stack Parameters

Modify `app.py` to customize:
- Stack name
- Environment (dev/staging/prod)
- Tags

## File Structure

```
infrastructure/
├── app.py                   # CDK app entry point
├── cdk.json                 # CDK configuration
├── multi_agent_stack.py     # Stack definition
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Troubleshooting

### "app is required" Error

**Solution**: Make sure you're in the `infrastructure` directory and `cdk.json` exists.

```bash
cd infrastructure
ls cdk.json  # Should exist
cdk synth    # Should work now
```

### Error 9009 - Subprocess Exited

**Cause**: Python executable not found or wrong name (python3 vs python)

**Quick Fix**:
```bash
# The cdk.json now uses "python" instead of "python3"
# If still failing, try:

# Option 1: Run directly
python app.py

# Option 2: Use provided scripts
cdk.bat      # Windows
./cdk.sh     # Linux/Mac

# Option 3: Virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac
pip install -r requirements.txt
```

**Detailed Guide**: See [docs/CDK_ERROR_9009.md](../docs/CDK_ERROR_9009.md)

### Bootstrap Error

**Solution**: Bootstrap your AWS account:

```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

### Permission Errors

**Solution**: Ensure your AWS credentials have sufficient permissions:
- CloudFormation
- Lambda
- DynamoDB
- API Gateway
- IAM
- Step Functions
- EventBridge

### Deployment Timeout

**Solution**: Increase Lambda timeout in `multi_agent_stack.py`:

```python
timeout=Duration.seconds(600)  # Increase from 300
```

## Outputs

After deployment, the stack outputs:

- **DialogueAPIEndpoint**: API Gateway endpoint URL
- **ConversationTableName**: DynamoDB conversation table
- **SessionTableName**: DynamoDB session table

Get outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name ABSolutionMultiAgentStack \
  --query 'Stacks[0].Outputs'
```

## Cost Estimation

Monthly cost estimate (light usage):

- **Lambda**: ~$5-10 (1M requests)
- **DynamoDB**: ~$1-5 (on-demand)
- **API Gateway**: ~$3-5 (1M requests)
- **Bedrock**: Pay per token (~$10-50 depending on usage)
- **SageMaker**: ~$50-100 (if endpoint running 24/7)

**Total**: ~$70-170/month for light usage

## Security

### IAM Roles

Lambda functions use least-privilege IAM roles:
- Bedrock: `InvokeModel` only
- DynamoDB: Read/Write to specific tables
- SageMaker: `InvokeEndpoint` only

### API Security

For production, add authentication:

1. **API Key**:
```python
api_key = self.api.add_api_key("ABSolutionAPIKey")
```

2. **Cognito**:
```python
authorizer = apigateway.CognitoUserPoolsAuthorizer(...)
```

3. **Lambda Authorizer**:
```python
authorizer = apigateway.TokenAuthorizer(...)
```

### Data Encryption

- DynamoDB: Encryption at rest enabled
- API Gateway: HTTPS only
- Secrets: Use AWS Secrets Manager (not implemented yet)

## Monitoring

### CloudWatch Logs

View logs:

```bash
# Lambda logs
aws logs tail /aws/lambda/abs-agent-coordinator --follow

# API Gateway logs
aws logs tail /aws/apigateway/abs-dialogue-api --follow
```

### Metrics

Key metrics to monitor:
- Lambda invocations
- API Gateway requests
- DynamoDB read/write capacity
- Lambda errors and duration

### Alarms

Add CloudWatch alarms for:
- Lambda errors > threshold
- API Gateway 5xx errors
- DynamoDB throttling

## Updates

### Update Lambda Code

```bash
# Make changes to src/agents/
# Then redeploy
cdk deploy ABSolutionMultiAgentStack
```

### Update Infrastructure

```bash
# Edit multi_agent_stack.py
# Then deploy
cdk deploy ABSolutionMultiAgentStack
```

## Cleanup

### Remove All Resources

```bash
cdk destroy ABSolutionMultiAgentStack
```

**Warning**: This will delete:
- All Lambda functions
- DynamoDB tables (and data)
- API Gateway
- IAM roles
- Step Functions

### Retain Data

To keep DynamoDB data, change in `multi_agent_stack.py`:

```python
removal_policy=RemovalPolicy.RETAIN
```

## Best Practices

1. **Use Separate Stacks**: Dev, Staging, Prod
2. **Enable Point-in-Time Recovery**: For DynamoDB
3. **Add Alarms**: For error rates and costs
4. **Use Secrets Manager**: For API keys
5. **Enable VPC**: For sensitive workloads
6. **Tag Resources**: For cost tracking

## Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [Multi-Agent System Docs](../docs/multi_agent_system.md)
