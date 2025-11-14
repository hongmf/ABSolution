# AWS Deployment Guide for ABSolution

This guide walks you through deploying the ABSolution AWS-native ABS Analytics Platform to your AWS account.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed (version 2.x or higher)
- Python 3.11+ installed
- Node.js and npm installed (for deployment scripts)
- Git installed

## Step 1: Install and Configure AWS CLI

### Install AWS CLI

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**macOS:**
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

**Windows:**
Download and run the AWS CLI MSI installer from:
https://awscli.amazonaws.com/AWSCLIV2.msi

### Verify Installation

```bash
aws --version
```

## Step 2: Configure AWS Credentials

You have your AWS access credentials ready. Now configure them:

### Method 1: Using AWS Configure (Recommended)

```bash
aws configure
```

When prompted, enter:
- **AWS Access Key ID**: Your access key
- **AWS Secret Access Key**: Your secret key
- **Default region name**: `us-east-1` (or your preferred region)
- **Default output format**: `json`

### Method 2: Manual Configuration

Create/edit `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY_HERE
aws_secret_access_key = YOUR_SECRET_KEY_HERE
```

Create/edit `~/.aws/config`:
```ini
[default]
region = us-east-1
output = json
```

### Verify AWS Configuration

```bash
aws sts get-caller-identity
```

This should return your AWS account details.

## Step 3: Get Your AWS Account ID

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Your AWS Account ID: $AWS_ACCOUNT_ID"
```

## Step 4: Set Up Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and update:
```bash
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=YOUR_ACTUAL_ACCOUNT_ID
ALERT_EMAIL=your-email@example.com
ENVIRONMENT=dev
```

## Step 5: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (if any)
npm install
```

## Step 6: Deploy Infrastructure

### Option A: Using the Master Deployment Script (Recommended)

```bash
bash scripts/deploy_all.sh
```

This script will:
1. Validate your AWS credentials
2. Deploy the CloudFormation stack
3. Package and deploy Lambda functions
4. Set up Glue jobs
5. Configure SageMaker endpoints
6. Display all deployment outputs

### Option B: Manual Step-by-Step Deployment

#### 6.1 Deploy CloudFormation Stack

```bash
npm run deploy:stack
```

Or manually:
```bash
aws cloudformation create-stack \
  --stack-name absolution-platform-dev \
  --template-body file://infrastructure/cloudformation/main-stack.yaml \
  --parameters ParameterKey=Environment,ParameterValue=dev \
               ParameterKey=AlertEmail,ParameterValue=your-email@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Monitor stack creation:
```bash
aws cloudformation wait stack-create-complete \
  --stack-name absolution-platform-dev
```

Or check status:
```bash
aws cloudformation describe-stacks \
  --stack-name absolution-platform-dev \
  --query 'Stacks[0].StackStatus'
```

#### 6.2 Deploy Lambda Functions

```bash
npm run deploy:lambda
```

Or manually:
```bash
bash scripts/deploy_lambda.sh
```

#### 6.3 Deploy Glue Jobs

```bash
npm run deploy:glue
```

Or manually:
```bash
bash scripts/deploy_glue.sh
```

#### 6.4 Deploy SageMaker Model (Optional)

```bash
npm run deploy:sagemaker
```

Or manually:
```bash
bash scripts/deploy_sagemaker.sh
```

## Step 7: Verify Deployment

### Check Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name absolution-platform-dev \
  --query 'Stacks[0].Outputs' \
  --output table
```

### Test API Endpoint

```bash
API_URL=$(aws cloudformation describe-stacks \
  --stack-name absolution-platform-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
  --output text)

echo "API Endpoint: $API_URL"

curl $API_URL/health
```

### Verify S3 Buckets

```bash
aws s3 ls | grep abs-solution
```

### Verify DynamoDB Tables

```bash
aws dynamodb list-tables | grep abs-
```

### Verify Lambda Functions

```bash
aws lambda list-functions | grep abs-
```

## Step 8: Configure Additional Services

### Enable Bedrock Access

1. Go to AWS Console > Amazon Bedrock
2. Request model access for: `anthropic.claude-3-sonnet`
3. Wait for approval (usually instant)

### Set Up QuickSight (Optional)

1. Go to AWS Console > QuickSight
2. Sign up for QuickSight if not already done
3. Create a dataset connected to your Glue database
4. Import the dashboard template (if available)

### Configure Lake Formation (Optional)

1. Go to AWS Console > Lake Formation
2. Add your Glue database to Lake Formation
3. Configure data permissions as needed

## Step 9: Upload Sample Data (Optional)

Upload sample SEC filings to test:

```bash
# Get bucket name
RAW_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name absolution-platform-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`RawDataBucketName`].OutputValue' \
  --output text)

# Upload sample data
aws s3 cp sample-data/ s3://$RAW_BUCKET/sec-filings/ --recursive
```

## Step 10: Monitor Your Deployment

### CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/abs-filing-normalizer-dev --follow
```

### CloudWatch Metrics

Go to CloudWatch Console to view:
- Lambda invocations and errors
- DynamoDB read/write capacity
- Kinesis stream metrics
- API Gateway requests

## Updating the Stack

To update your deployment after making changes:

```bash
npm run update:stack
```

Or manually:
```bash
aws cloudformation update-stack \
  --stack-name absolution-platform-dev \
  --template-body file://infrastructure/cloudformation/main-stack.yaml \
  --parameters ParameterKey=Environment,ParameterValue=dev \
               ParameterKey=AlertEmail,ParameterValue=your-email@example.com \
  --capabilities CAPABILITY_NAMED_IAM
```

## Deleting the Stack

To remove all resources:

```bash
npm run delete:stack
```

Or manually:
```bash
aws cloudformation delete-stack --stack-name absolution-platform-dev
```

**Warning:** This will delete all resources including S3 buckets (if empty) and DynamoDB tables. Make sure to backup any important data first.

## Troubleshooting

### Issue: "Unable to locate credentials"

**Solution:** Run `aws configure` again and ensure credentials are correct.

### Issue: "Stack creation failed"

**Solution:** Check CloudFormation events:
```bash
aws cloudformation describe-stack-events \
  --stack-name absolution-platform-dev \
  --max-items 10
```

### Issue: "Access Denied" errors

**Solution:** Ensure your IAM user has the following permissions:
- CloudFormation: Full access
- IAM: Create/manage roles
- S3: Full access
- Lambda: Full access
- DynamoDB: Full access
- Kinesis: Full access
- API Gateway: Full access
- SageMaker: Full access (if using ML features)
- Bedrock: Full access (if using AI features)

### Issue: "Lambda deployment failed"

**Solution:**
1. Check that the Lambda code exists in `src/lambda/`
2. Ensure dependencies are packaged correctly
3. Verify the Lambda execution role has proper permissions

### Issue: "Bedrock model not available"

**Solution:** Request model access in Bedrock console and wait for approval.

## Cost Estimation

Running this platform will incur AWS costs. Here's an approximate breakdown:

- **S3**: ~$5-20/month (depends on data volume)
- **DynamoDB**: ~$5-10/month (with on-demand pricing)
- **Lambda**: ~$5-20/month (depends on invocations)
- **Kinesis**: ~$15/month (2 shards)
- **SageMaker**: ~$50-200/month (if endpoint is running)
- **Bedrock**: Pay per API call (~$3-15 per 1M tokens)
- **API Gateway**: ~$3.50 per million requests

**Total Estimated Cost**: $100-300/month depending on usage

### Cost Optimization Tips:

1. Use S3 Lifecycle policies to archive old data
2. Stop SageMaker endpoints when not in use
3. Use Lambda instead of always-on servers
4. Enable DynamoDB auto-scaling
5. Monitor and set up billing alerts

## Next Steps

1. Explore the API documentation: `docs/API.md`
2. Review the architecture diagram: `docs/ARCHITECTURE.md`
3. Run tests: `npm run test:local`
4. Set up CI/CD pipeline (GitHub Actions template available)
5. Configure monitoring dashboards in CloudWatch

## Support

For issues or questions:
- Check the documentation in `docs/`
- Review CloudFormation events and CloudWatch logs
- Consult AWS documentation for specific services

## Security Best Practices

1. Never commit `.env` file or AWS credentials to git
2. Use AWS Secrets Manager for sensitive data
3. Enable MFA on your AWS account
4. Regularly rotate access keys
5. Use least-privilege IAM policies
6. Enable CloudTrail for audit logging
7. Review S3 bucket policies regularly
8. Enable encryption at rest for all data stores

---

**Happy Deploying!**
