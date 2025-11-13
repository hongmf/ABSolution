# ABSolution Deployment Guide

Complete guide to deploying the ABSolution Multi-Agent AI System to AWS.

## Prerequisites

Before deploying, ensure you have:

### 1. AWS Account
- Active AWS account with appropriate permissions
- AWS credentials configured locally

### 2. Required Software
- **Node.js** (v14 or later) - [Download](https://nodejs.org/)
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **AWS CLI** - [Install Guide](https://aws.amazon.com/cli/)
- **AWS CDK** - Will be installed by setup script

### 3. AWS Permissions

Your IAM user/role needs permissions for:
- CloudFormation (full access)
- Lambda (create, update, invoke)
- DynamoDB (create, read, write)
- API Gateway (create, deploy)
- IAM (create roles, policies)
- Step Functions (create, execute)
- EventBridge (create rules)
- Bedrock (invoke models)
- SageMaker (optional, for ML models)

## Quick Deployment (Automated)

### Step 1: Run Setup

```bash
cd infrastructure
./setup.sh
```

This will:
- ✅ Check all prerequisites
- ✅ Install AWS CDK globally
- ✅ Install Python dependencies
- ✅ Verify AWS credentials
- ✅ Set environment variables

### Step 2: Deploy

```bash
# From project root
./scripts/deploy_agents.sh
```

This automated script will:
1. Check prerequisites
2. Install dependencies
3. Bootstrap CDK (if needed)
4. Package Lambda functions
5. Deploy infrastructure stack
6. Output API endpoint

**Estimated time**: 10-15 minutes

### Step 3: Configure Bedrock

After deployment, enable Bedrock models (Console only):

```bash
# MUST use AWS Console - no CLI option available:
# 1. Go to Amazon Bedrock console
# 2. Navigate to "Model access"
# 3. Click "Request model access"
# 4. Enable "Claude 3 Haiku" or "Claude 3.5 Sonnet"
# 5. Wait for approval (usually instant)
```

### Step 4: Test

```bash
# Get API endpoint from deployment output
export API_ENDPOINT="https://8behc61ju4.execute-api.us-east-1.amazonaws.com/prod"

# Test session creation
curl -X POST $API_ENDPOINT/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test"}'

# Test message sending
curl -X POST $API_ENDPOINT/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "message": "What is ABS?"
  }'
```

## Manual Deployment (Step-by-Step)

### Step 1: Configure AWS

```bash
# Configure credentials
aws configure

# Verify
aws sts get-caller-identity
```

### Step 2: Install Dependencies

```bash
# Install Node.js dependencies (for CDK)
npm install -g aws-cdk

# Install Python dependencies
pip install -r requirements.txt

# Install CDK dependencies
cd infrastructure
pip install -r requirements.txt
cd ..
```

### Step 3: Bootstrap CDK

**First time only** - prepares your AWS account for CDK:

```bash
cd infrastructure

# Set environment
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION=us-east-1

# Bootstrap
cdk bootstrap aws://$CDK_DEFAULT_ACCOUNT/$CDK_DEFAULT_REGION
```

### Step 4: Review Stack

```bash
# Synthesize CloudFormation template
cdk synth ABSolutionMultiAgentStack

# Review what will be created
cdk diff ABSolutionMultiAgentStack
```

### Step 5: Deploy

```bash
# Deploy the stack
cdk deploy ABSolutionMultiAgentStack

# Accept prompts with 'y'
```

**Deployment creates:**
- 7 Lambda functions (1 coordinator + 5 agents + 1 API handler)
- 2 DynamoDB tables (conversations + sessions)
- 1 API Gateway (REST API with 4 endpoints)
- 1 Step Functions workflow
- 2 EventBridge rules
- IAM roles and policies

### Step 6: Get Outputs

```bash
# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name ABSolutionMultiAgentStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DialogueAPIEndpoint`].OutputValue' \
  --output text
```

## Troubleshooting

### Error: "--app is required"

**Cause**: CDK can't find the app configuration

**Solution**:
```bash
# Make sure you're in the infrastructure directory
cd infrastructure

# Verify cdk.json exists
ls cdk.json

# Try again
cdk synth
```

### Error: "Need to perform AWS calls"

**Cause**: AWS credentials not configured

**Solution**:
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (e.g., us-east-1)
```

### Error: "This stack uses assets"

**Cause**: CDK bootstrap not run

**Solution**:
```bash
cd infrastructure
cdk bootstrap
```

### Error: Lambda code too large

**Cause**: Lambda package exceeds size limits

**Solution**:
```bash
# Use Lambda layers for dependencies
# Or reduce dependencies in requirements.txt
```

### Error: Bedrock access denied

**Cause**: Bedrock models not enabled

**Solution**:
1. Go to AWS Console → Bedrock
2. Click "Model access"
3. Enable Claude models
4. Wait for approval

### Deployment hangs or times out

**Cause**: Network issues or resource limits

**Solution**:
```bash
# Increase timeout in multi_agent_stack.py
timeout=Duration.seconds(600)

# Or check CloudWatch logs
aws logs tail /aws/lambda/abs-agent-coordinator --follow
```

## Post-Deployment

### 1. Test the API

```bash
# Test locally
python scripts/test_agents.py YOUR_API_ENDPOINT
```

### 2. Start the UI

```bash
# Start web interface
python3 scripts/serve_ui.py

# Open http://localhost:8080
# Configure with your API endpoint
```

### 3. Monitor

```bash
# View Lambda logs
aws logs tail /aws/lambda/abs-agent-coordinator --follow

# View API Gateway logs
aws logs tail /aws/apigateway/abs-dialogue-api --follow
```

### 4. Set Up Alarms (Recommended)

```bash
# Create alarm for Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name abs-lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Optional: Deploy SageMaker Model

For ML-based risk scoring:

```bash
# Train model
python src/sagemaker/train_risk_model.py

# Deploy endpoint
python src/sagemaker/inference.py --deploy

# Update Lambda environment variable
aws lambda update-function-configuration \
  --function-name abs-agent-coordinator \
  --environment Variables={SAGEMAKER_RISK_ENDPOINT=abs-risk-scoring-model}
```

## Cost Optimization

### Development Environment

```bash
# Use smaller Lambda memory
memory_size=512

# Use DynamoDB on-demand billing
billing_mode=BillingMode.PAY_PER_REQUEST

# Reduce Lambda timeout
timeout=Duration.seconds(60)
```

### Production Environment

```bash
# Enable Lambda reserved concurrency
reserved_concurrent_executions=10

# Enable DynamoDB auto-scaling
auto_scaling_enabled=True

# Enable API Gateway caching
cache_enabled=True
```

## Updates and Maintenance

### Update Lambda Code

```bash
# Make changes to src/agents/
# Then redeploy
cd infrastructure
cdk deploy ABSolutionMultiAgentStack
```

### Update Infrastructure

```bash
# Edit infrastructure/multi_agent_stack.py
# Then deploy
cd infrastructure
cdk deploy ABSolutionMultiAgentStack
```

### View Deployment History

```bash
aws cloudformation describe-stack-events \
  --stack-name ABSolutionMultiAgentStack \
  --max-items 20
```

## Cleanup

### Remove All Resources

```bash
cd infrastructure
cdk destroy ABSolutionMultiAgentStack

# Confirm with 'y'
```

**This will delete:**
- All Lambda functions
- DynamoDB tables (and data!)
- API Gateway
- IAM roles
- Step Functions
- EventBridge rules

### Retain DynamoDB Data

Before destroying, export data:

```bash
# Export conversation data
aws dynamodb scan \
  --table-name abs-agent-conversations \
  --output json > conversations_backup.json

# Export session data
aws dynamodb scan \
  --table-name abs-agent-sessions \
  --output json > sessions_backup.json
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy ABSolution

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - uses: actions/setup-python@v2

      - name: Install CDK
        run: npm install -g aws-cdk

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          cd infrastructure
          pip install -r requirements.txt

      - name: Deploy
        run: |
          cd infrastructure
          cdk deploy ABSolutionMultiAgentStack --require-approval never
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-east-1
```

## Security Best Practices

1. **Use Secrets Manager** for API keys
2. **Enable VPC** for Lambda functions
3. **Use API Gateway authorizers** (Cognito or Lambda)
4. **Enable CloudTrail** for audit logging
5. **Use KMS** for encryption at rest
6. **Implement rate limiting** on API Gateway
7. **Use WAF** for API protection

## Monitoring and Logging

### CloudWatch Dashboards

Create a dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name ABSolution \
  --dashboard-body file://dashboard.json
```

### X-Ray Tracing

Enable in `multi_agent_stack.py`:

```python
tracing=lambda_.Tracing.ACTIVE
```

## Support

If you encounter issues:

1. Check [Troubleshooting](#troubleshooting) section
2. Review CloudWatch logs
3. Check [infrastructure/README.md](infrastructure/README.md)
4. See [docs/multi_agent_system.md](docs/multi_agent_system.md)

## Next Steps

After successful deployment:

1. ✅ Test the API endpoints
2. ✅ Start the web UI
3. ✅ Enable Bedrock models
4. ✅ Set up monitoring and alarms
5. ✅ Configure authentication (production)
6. ✅ Deploy SageMaker models (optional)
7. ✅ Set up CI/CD pipeline (production)

**You're ready to use ABSolution!** 🎉
