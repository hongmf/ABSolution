# ABSolution - Quick Start Guide

Get your ABSolution platform deployed to AWS in minutes!

## Prerequisites

- AWS account with admin access
- AWS Access Key ID and Secret Access Key
- Email address for alerts

## Quick Deployment (3 Simple Steps)

### Step 1: Configure AWS Credentials

Run the configuration script:

```bash
bash scripts/configure_aws.sh
```

This will:
- Check if AWS CLI is installed
- Configure your AWS credentials
- Set up your `.env` file
- Verify IAM permissions

### Step 2: Deploy Everything

Run the master deployment script:

```bash
bash scripts/deploy_all.sh
```

This will:
- Deploy CloudFormation infrastructure (S3, DynamoDB, Kinesis, Lambda, etc.)
- Package and deploy Lambda functions
- Set up AWS Glue jobs
- Verify all resources
- Display deployment summary

**Time:** ~10-15 minutes

### Step 3: Verify Deployment

After deployment completes, test your API:

```bash
# Get API endpoint from deployment output
curl https://YOUR-API-ENDPOINT.execute-api.us-east-1.amazonaws.com/dev
```

## What Gets Deployed?

Your ABSolution platform includes:

### Core Infrastructure
- **3 S3 Buckets**: Raw data, processed data, and model artifacts
- **3 DynamoDB Tables**: Filings, risk scores, and alerts
- **1 Kinesis Stream**: Real-time SEC filings stream
- **1 SNS Topic**: Alert notifications
- **1 API Gateway**: Benchmark API endpoint

### Compute & Processing
- **4 Lambda Functions**:
  - Filing Normalizer (processes SEC filings)
  - Risk Scorer (ML-based risk assessment)
  - Alert Handler (manages notifications)
  - Benchmark API (REST API for data access)

### Data & Analytics
- **AWS Glue Database**: Data catalog
- **IAM Roles**: Proper security permissions
- **CloudWatch Logs**: Monitoring and logging

### AI/ML Ready
- **SageMaker**: Ready for model training/deployment
- **Bedrock**: For generative AI insights
- **Comprehend**: NLP sentiment analysis
- **Textract**: PDF data extraction

## Next Steps After Deployment

### 1. Upload Sample Data

```bash
# Get your raw data bucket name
RAW_BUCKET=$(cat deployment-info.json | jq -r '.raw_bucket')

# Upload sample SEC filings (if you have them)
aws s3 cp ./sample-data/ s3://$RAW_BUCKET/sec-filings/ --recursive
```

### 2. Monitor Your Functions

```bash
# Watch Lambda logs in real-time
aws logs tail /aws/lambda/abs-filing-normalizer-dev --follow
```

### 3. Access AWS Console

View your resources:
- **S3**: https://s3.console.aws.amazon.com/s3/
- **DynamoDB**: https://console.aws.amazon.com/dynamodb/
- **Lambda**: https://console.aws.amazon.com/lambda/
- **CloudWatch**: https://console.aws.amazon.com/cloudwatch/

### 4. Customize Your Deployment

Edit the configuration:
```bash
# Edit environment variables
nano .env

# Edit CloudFormation template
nano infrastructure/cloudformation/main-stack.yaml

# Update stack
npm run update:stack
```

## Manual Deployment (Alternative)

If you prefer step-by-step manual deployment:

### 1. Install AWS CLI

```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 2. Configure Credentials

```bash
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Enter region: us-east-1
# Enter output format: json
```

### 3. Create .env File

```bash
cp .env.example .env
# Edit .env with your AWS Account ID and email
```

### 4. Deploy CloudFormation Stack

```bash
npm run deploy:stack
```

### 5. Deploy Lambda Functions

```bash
npm run deploy:lambda
```

## Estimated Costs

Monthly AWS costs (approximate):

| Service | Cost |
|---------|------|
| S3 Storage | $5-20 |
| DynamoDB | $5-10 |
| Lambda | $5-20 |
| Kinesis | $15 |
| API Gateway | $3.50/million requests |
| CloudWatch | $5 |
| **Total (base)** | **~$40-75/month** |

*Additional costs for SageMaker, Bedrock usage*

## Common Issues

### "Unable to locate credentials"

**Solution:**
```bash
aws configure
# Re-enter your credentials
```

### "Access Denied" errors

**Solution:** Ensure your IAM user has these permissions:
- CloudFormation (full)
- IAM (create roles)
- S3, Lambda, DynamoDB, Kinesis, API Gateway (full)

### Stack creation failed

**Solution:**
```bash
# Check error details
aws cloudformation describe-stack-events \
  --stack-name absolution-platform-dev \
  --max-items 5
```

## Useful Commands

```bash
# View stack status
aws cloudformation describe-stacks \
  --stack-name absolution-platform-dev \
  --query 'Stacks[0].StackStatus'

# List all S3 buckets
aws s3 ls | grep abs-solution

# List DynamoDB tables
aws dynamodb list-tables | grep abs-

# List Lambda functions
aws lambda list-functions | grep abs-

# View Lambda function logs
aws logs tail /aws/lambda/abs-filing-normalizer-dev --follow

# Update the stack
npm run update:stack

# Delete everything (WARNING: destructive!)
npm run delete:stack
```

## Documentation

For detailed documentation:

- **Full Deployment Guide**: [docs/deployment/AWS_DEPLOYMENT_GUIDE.md](docs/deployment/AWS_DEPLOYMENT_GUIDE.md)
- **Architecture Overview**: README.md
- **AWS Configuration**: config/aws_config.yaml

## Support

Having issues? Check:

1. AWS CloudFormation Events in AWS Console
2. CloudWatch Logs for Lambda functions
3. Your IAM permissions
4. AWS Service Quotas

## Clean Up (Remove All Resources)

When you're done:

```bash
npm run delete:stack
```

**Warning:** This will delete all resources. Make sure to backup any important data first!

---

**Ready to deploy? Run:** `bash scripts/configure_aws.sh`
