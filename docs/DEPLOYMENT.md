# ABSolution Deployment Guide

This guide covers the complete deployment of the ABSolution ABS Analytics Platform on AWS.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Deployment Steps](#deployment-steps)
- [Configuration](#configuration)
- [Testing](#testing)
- [Monitoring](#monitoring)

## Prerequisites

### Required Tools
- AWS CLI v2 (configured with appropriate credentials)
- Python 3.11+
- AWS SAM CLI (optional, for local testing)
- Node.js 18+ (for deployment scripts)
- Git

### Required AWS Services Access
- AWS Glue
- AWS Lambda
- Amazon S3
- Amazon DynamoDB
- Amazon Kinesis
- Amazon SageMaker
- Amazon Bedrock (Claude model access required)
- Amazon Textract
- Amazon Comprehend
- Amazon QuickSight (for dashboards)
- Amazon Neptune (optional, for graph analytics)
- AWS Lake Formation
- API Gateway
- EventBridge
- SNS
- CloudWatch

### IAM Permissions
Your AWS user/role needs permissions to:
- Create and manage CloudFormation stacks
- Create IAM roles and policies
- Create and manage all services listed above

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       Data Ingestion Layer                       │
├─────────────────────────────────────────────────────────────────┤
│  SEC EDGAR API → Kinesis Stream → Lambda Normalizer → S3/DynamoDB│
│                      ↓                                            │
│                 AWS Glue ETL                                     │
│                      ↓                                            │
│              Amazon Textract (PDF Extraction)                    │
│                      ↓                                            │
│            Amazon Comprehend (NLP Analysis)                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Analytics Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  SageMaker → Risk Scoring → EventBridge Alerts → SNS            │
│                      ↓                                            │
│              Amazon Bedrock (AI Narratives)                      │
│                      ↓                                            │
│            QuickSight Dashboards                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                 │
├─────────────────────────────────────────────────────────────────┤
│     API Gateway → Lambda Functions → DynamoDB                    │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Steps

### Step 1: Clone and Setup

```bash
git clone <repository-url>
cd ABSolution

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp config/aws_config.yaml config/aws_config.local.yaml
# Edit aws_config.local.yaml with your AWS account details
```

### Step 2: Deploy Infrastructure

```bash
# Deploy CloudFormation stack
aws cloudformation create-stack \
  --stack-name absolution-platform-dev \
  --template-body file://infrastructure/cloudformation/main-stack.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=AlertEmail,ParameterValue=your-email@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Wait for stack creation
aws cloudformation wait stack-create-complete \
  --stack-name absolution-platform-dev \
  --region us-east-1

# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name absolution-platform-dev \
  --query 'Stacks[0].Outputs' \
  --region us-east-1
```

### Step 3: Deploy Lambda Functions

```bash
# Package Lambda functions
cd src/lambda

# Package Filing Normalizer
zip -r filing_normalizer.zip filing_normalizer.py
aws lambda update-function-code \
  --function-name abs-filing-normalizer-dev \
  --zip-file fileb://filing_normalizer.zip \
  --region us-east-1

# Package Risk Scorer
zip -r risk_scorer.zip risk_scorer.py
aws lambda update-function-code \
  --function-name abs-risk-scorer-dev \
  --zip-file fileb://risk_scorer.zip \
  --region us-east-1

# Package Alert Handler
zip -r alert_handler.zip alert_handler.py
aws lambda update-function-code \
  --function-name abs-alert-handler-dev \
  --zip-file fileb://alert_handler.zip \
  --region us-east-1

cd ../api
zip -r benchmark_api.zip benchmark_api.py
aws lambda update-function-code \
  --function-name abs-benchmark-api-dev \
  --zip-file fileb://benchmark_api.zip \
  --region us-east-1

cd ../bedrock
zip -r narrative_generator.zip narrative_generator.py
aws lambda update-function-code \
  --function-name abs-narrative-generator-dev \
  --zip-file fileb://narrative_generator.zip \
  --region us-east-1

cd ../..
```

### Step 4: Deploy Glue Jobs

```bash
# Upload Glue script to S3
PROCESSED_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name absolution-platform-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ProcessedDataBucketName`].OutputValue' \
  --output text \
  --region us-east-1)

aws s3 cp src/glue/sec_filings_ingest.py \
  s3://${PROCESSED_BUCKET}/scripts/ \
  --region us-east-1

# Create Glue job
aws glue create-job \
  --name sec-filings-etl-dev \
  --role abs-glue-service-role-dev \
  --command Name=glueetl,ScriptLocation=s3://${PROCESSED_BUCKET}/scripts/sec_filings_ingest.py \
  --default-arguments '{
    "--JOB_NAME": "sec-filings-etl-dev",
    "--S3_INPUT_PATH": "s3://abs-solution-raw-data-dev/sec-filings/",
    "--S3_OUTPUT_PATH": "s3://abs-solution-processed-data-dev/normalized/",
    "--DATABASE_NAME": "abs_analytics_db_dev"
  }' \
  --glue-version "4.0" \
  --worker-type "G.1X" \
  --number-of-workers 2 \
  --region us-east-1
```

### Step 5: Train and Deploy SageMaker Model

```bash
# Upload training data to S3 (if you have it)
RAW_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name absolution-platform-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`RawDataBucketName`].OutputValue' \
  --output text \
  --region us-east-1)

# Run training locally or on SageMaker
cd src/sagemaker
python train_risk_model.py \
  --model-type xgboost \
  --n-samples 10000 \
  --model-dir ./model

# Package model for SageMaker
tar -czf model.tar.gz -C model .

# Upload to S3
MODEL_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name absolution-platform-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ModelArtifactsBucketName`].OutputValue' \
  --output text \
  --region us-east-1)

aws s3 cp model.tar.gz s3://${MODEL_BUCKET}/models/risk-scorer/ --region us-east-1

# Create SageMaker model
aws sagemaker create-model \
  --model-name abs-risk-model-dev \
  --primary-container Image=683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1,ModelDataUrl=s3://${MODEL_BUCKET}/models/risk-scorer/model.tar.gz \
  --execution-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/abs-sagemaker-execution-role-dev \
  --region us-east-1

# Create endpoint configuration
aws sagemaker create-endpoint-config \
  --endpoint-config-name abs-risk-scoring-endpoint-config-dev \
  --production-variants VariantName=primary,ModelName=abs-risk-model-dev,InstanceType=ml.t2.medium,InitialInstanceCount=1 \
  --region us-east-1

# Create endpoint
aws sagemaker create-endpoint \
  --endpoint-name abs-risk-scoring-endpoint-dev \
  --endpoint-config-name abs-risk-scoring-endpoint-config-dev \
  --region us-east-1

# Wait for endpoint to be in service
aws sagemaker wait endpoint-in-service \
  --endpoint-name abs-risk-scoring-endpoint-dev \
  --region us-east-1
```

### Step 6: Set Up Kinesis Producer

```bash
# Run Kinesis producer to start streaming data
cd src/kinesis
python sec_filings_producer.py --mode continuous --interval 300 &
```

### Step 7: Configure QuickSight (Manual)

1. Go to AWS QuickSight console
2. Create a new dataset from DynamoDB:
   - Select `abs-filings-dev` table
   - Select `abs-risk-scores-dev` table
3. Create visualizations:
   - Delinquency trends over time
   - Risk score distribution
   - Asset class performance comparison
   - Top high-risk issuers
4. Create dashboard and share with stakeholders

### Step 8: Set Up Lake Formation Security (Optional)

```bash
# Register S3 locations
aws lakeformation register-resource \
  --resource-arn arn:aws:s3:::${PROCESSED_BUCKET} \
  --use-service-linked-role \
  --region us-east-1

# Grant permissions (adjust principals as needed)
aws lakeformation grant-permissions \
  --principal DataLakePrincipalIdentifier=arn:aws:iam::ACCOUNT_ID:role/DataAnalystRole \
  --permissions SELECT DESCRIBE \
  --resource '{
    "Table": {
      "DatabaseName": "abs_analytics_db_dev",
      "Name": "normalized_sec_filings"
    }
  }' \
  --region us-east-1
```

## Configuration

### Environment Variables

Update `config/aws_config.yaml` with your specific values:

```yaml
aws:
  region: us-east-1
  account_id: YOUR_ACCOUNT_ID

s3:
  raw_data_bucket: abs-solution-raw-data-dev-YOUR_ACCOUNT_ID
  processed_data_bucket: abs-solution-processed-data-dev-YOUR_ACCOUNT_ID
  model_artifacts_bucket: abs-solution-model-artifacts-dev-YOUR_ACCOUNT_ID
```

### Bedrock Model Access

Enable Bedrock model access in AWS Console:
1. Go to Amazon Bedrock console
2. Navigate to "Model access"
3. Request access to "Anthropic Claude 3 Sonnet"
4. Wait for approval (usually instant)

## Testing

### Test Lambda Functions

```bash
# Test Filing Normalizer
aws lambda invoke \
  --function-name abs-filing-normalizer-dev \
  --payload file://tests/sample_filing.json \
  --region us-east-1 \
  response.json

cat response.json

# Test Risk Scorer
aws lambda invoke \
  --function-name abs-risk-scorer-dev \
  --payload file://tests/sample_normalized_filing.json \
  --region us-east-1 \
  response.json

# Test Benchmark API
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev/benchmark/issuer/0001234567
```

### Test Kinesis Stream

```bash
cd src/kinesis
python sec_filings_producer.py --mode produce --count 10
```

### Test Glue Job

```bash
aws glue start-job-run \
  --job-name sec-filings-etl-dev \
  --region us-east-1
```

## Monitoring

### CloudWatch Dashboards

Create a CloudWatch dashboard to monitor:
- Lambda execution metrics (invocations, errors, duration)
- Kinesis stream metrics (incoming records, iterator age)
- DynamoDB metrics (read/write capacity, throttles)
- SageMaker endpoint metrics (invocations, latency)
- API Gateway metrics (requests, latency, errors)

### Alarms

Set up CloudWatch alarms for:
- Lambda errors > 5 in 5 minutes
- Kinesis iterator age > 60000 ms
- SageMaker endpoint errors
- High-risk alerts

### Logs

Access logs in CloudWatch:
```bash
# View Lambda logs
aws logs tail /aws/lambda/abs-filing-normalizer-dev --follow

# View Glue logs
aws logs tail /aws-glue/jobs/output --follow
```

## Cost Optimization

1. **S3**: Enable lifecycle policies to archive old data to Glacier
2. **DynamoDB**: Use on-demand billing or right-size provisioned capacity
3. **SageMaker**: Use serverless inference for low-traffic endpoints
4. **Lambda**: Optimize memory settings based on actual usage
5. **Kinesis**: Adjust shard count based on throughput requirements

## Troubleshooting

### Common Issues

1. **Lambda timeout**: Increase timeout in CloudFormation template
2. **SageMaker endpoint unavailable**: Check endpoint status and logs
3. **Bedrock access denied**: Ensure model access is granted
4. **Glue job fails**: Check IAM permissions and S3 paths
5. **API Gateway 502 errors**: Check Lambda function logs

## Security Best Practices

1. Enable encryption at rest for all S3 buckets
2. Use VPC endpoints for AWS services
3. Enable CloudTrail for audit logging
4. Use AWS Secrets Manager for sensitive configuration
5. Implement least privilege IAM policies
6. Enable MFA for privileged accounts
7. Use AWS WAF for API Gateway protection

## Cleanup

To delete all resources:

```bash
# Delete SageMaker endpoint
aws sagemaker delete-endpoint --endpoint-name abs-risk-scoring-endpoint-dev
aws sagemaker delete-endpoint-config --endpoint-config-name abs-risk-scoring-endpoint-config-dev
aws sagemaker delete-model --model-name abs-risk-model-dev

# Delete CloudFormation stack (this deletes most resources)
aws cloudformation delete-stack --stack-name absolution-platform-dev

# Empty and delete S3 buckets manually (CloudFormation won't delete non-empty buckets)
aws s3 rm s3://abs-solution-raw-data-dev-ACCOUNT_ID --recursive
aws s3 rb s3://abs-solution-raw-data-dev-ACCOUNT_ID

aws s3 rm s3://abs-solution-processed-data-dev-ACCOUNT_ID --recursive
aws s3 rb s3://abs-solution-processed-data-dev-ACCOUNT_ID

aws s3 rm s3://abs-solution-model-artifacts-dev-ACCOUNT_ID --recursive
aws s3 rb s3://abs-solution-model-artifacts-dev-ACCOUNT_ID
```

## Support

For issues or questions:
- Create an issue in the GitHub repository
- Contact the development team
- Refer to AWS documentation for service-specific issues
