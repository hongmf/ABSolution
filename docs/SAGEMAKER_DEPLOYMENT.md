# AWS SageMaker Deployment Guide

Complete guide for deploying the ABSolution risk scoring model to AWS SageMaker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Manual Deployment (AWS Console)](#manual-deployment-aws-console)
5. [Testing the Endpoint](#testing-the-endpoint)
6. [Troubleshooting](#troubleshooting)
7. [Cost Estimation](#cost-estimation)

---

## Prerequisites

### 1. AWS Account Setup

- Active AWS account
- AWS CLI configured with credentials
- Appropriate IAM permissions for SageMaker, S3, and IAM

### 2. Configure AWS CLI

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (e.g., `json`)

### 3. Verify AWS Credentials

```bash
aws sts get-caller-identity
```

### 4. Install Required Python Packages

```bash
pip install boto3 sagemaker scikit-learn xgboost joblib
```

---

## Quick Start

### Automated Deployment (Recommended)

Deploy everything with a single command:

```bash
python3 deploy_sagemaker.py
```

This will:
1. ✅ Create IAM role (if needed)
2. ✅ Create S3 bucket for model artifacts
3. ✅ Train the model locally
4. ✅ Upload model to S3
5. ✅ Create SageMaker model
6. ✅ Create endpoint configuration
7. ✅ Deploy endpoint (5-10 minutes)

### Custom Deployment

```bash
# Specify region
python3 deploy_sagemaker.py --region us-west-2

# Specify instance type (for higher performance)
python3 deploy_sagemaker.py --instance-type ml.m5.large

# Custom endpoint name
python3 deploy_sagemaker.py --endpoint-name my-abs-endpoint

# Use existing IAM role
python3 deploy_sagemaker.py --role-arn arn:aws:iam::123456789012:role/MyRole
```

### Configure Dashboard

After deployment completes, add to your `.env` file:

```bash
SAGEMAKER_ENDPOINT_NAME=abs-risk-endpoint
AWS_REGION=us-east-1
```

Then start the dashboard:

```bash
./start_dashboard.sh
```

---

## Step-by-Step Deployment

### Step 1: Create IAM Role

Create an IAM role for SageMaker with the following policies:

**Trust Relationship:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Attach Policies:**
- `AmazonSageMakerFullAccess`
- `AmazonS3FullAccess`

**AWS CLI:**
```bash
# Create role
aws iam create-role \
  --role-name ABSolutionSageMakerRole \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name ABSolutionSageMakerRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

aws iam attach-role-policy \
  --role-name ABSolutionSageMakerRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### Step 2: Create S3 Bucket

```bash
aws s3 mb s3://absolution-sagemaker-models --region us-east-1
```

### Step 3: Train Model Locally

```bash
python3 src/sagemaker/train_risk_model.py \
  --model-type xgboost \
  --n-samples 10000 \
  --model-dir ./model
```

### Step 4: Package and Upload Model

```bash
# Create tarball
cd model
tar -czf ../model.tar.gz *
cd ..

# Upload to S3
aws s3 cp model.tar.gz s3://absolution-sagemaker-models/models/
```

### Step 5: Create SageMaker Model

```bash
aws sagemaker create-model \
  --model-name abs-risk-model \
  --primary-container Image=<sklearn-inference-image>,ModelDataUrl=s3://absolution-sagemaker-models/models/model.tar.gz \
  --execution-role-arn arn:aws:iam::ACCOUNT_ID:role/ABSolutionSageMakerRole
```

### Step 6: Create Endpoint Configuration

```bash
aws sagemaker create-endpoint-config \
  --endpoint-config-name abs-risk-config \
  --production-variants \
    VariantName=AllTraffic,\
ModelName=abs-risk-model,\
InstanceType=ml.t2.medium,\
InitialInstanceCount=1
```

### Step 7: Create Endpoint

```bash
aws sagemaker create-endpoint \
  --endpoint-name abs-risk-endpoint \
  --endpoint-config-name abs-risk-config
```

Wait for endpoint to be in service:

```bash
aws sagemaker describe-endpoint --endpoint-name abs-risk-endpoint
```

---

## Manual Deployment (AWS Console)

### 1. Navigate to SageMaker Console

1. Go to: https://console.aws.amazon.com/sagemaker/
2. Select your region (top-right corner)

### 2. Upload Model to S3

1. Go to S3 Console: https://s3.console.aws.amazon.com/
2. Create bucket: `absolution-sagemaker-models`
3. Upload `model.tar.gz` to `models/` folder

### 3. Create SageMaker Model

1. In SageMaker Console, click **Models** → **Create model**
2. Model name: `abs-risk-model`
3. IAM role: Select or create SageMaker execution role
4. Container input options: **Provide model artifacts and inference image**
5. Location of inference code: (leave blank for scikit-learn)
6. Location of model artifacts: `s3://absolution-sagemaker-models/models/model.tar.gz`
7. Container image: Use scikit-learn inference image for your region
8. Click **Create model**

### 4. Create Endpoint Configuration

1. Click **Endpoint configurations** → **Create endpoint configuration**
2. Name: `abs-risk-config`
3. Add production variant:
   - Model: `abs-risk-model`
   - Instance type: `ml.t2.medium`
   - Initial instance count: `1`
4. Click **Create endpoint configuration**

### 5. Create Endpoint

1. Click **Endpoints** → **Create endpoint**
2. Endpoint name: `abs-risk-endpoint`
3. Attach endpoint configuration: `abs-risk-config`
4. Click **Create endpoint**
5. Wait 5-10 minutes for status to be **InService**

---

## Testing the Endpoint

### Test with Python

```python
import boto3
import json

# Initialize runtime client
runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')

# Sample prediction payload
payload = {
    'instances': [[
        0.025,  # delinquency_30_days
        0.015,  # delinquency_60_days
        0.008,  # delinquency_90_plus_days
        0.01,   # cumulative_default_rate
        0.008,  # cumulative_loss_rate
        700,    # weighted_average_fico
        0.75,   # weighted_average_ltv
        0.35,   # weighted_average_dti
        0.85,   # pool_balance_ratio
        24,     # pool_seasoning_months
        0.08,   # credit_enhancement
        0.05,   # subordination_level
        12      # months_since_origination
    ]]
}

# Invoke endpoint
response = runtime.invoke_endpoint(
    EndpointName='abs-risk-endpoint',
    ContentType='application/json',
    Body=json.dumps(payload)
)

# Parse response
result = json.loads(response['Body'].read().decode())
print("Prediction:", result)
```

### Test with AWS CLI

```bash
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name abs-risk-endpoint \
  --content-type application/json \
  --body '{"instances":[[0.025,0.015,0.008,0.01,0.008,700,0.75,0.35,0.85,24,0.08,0.05,12]]}' \
  output.json

cat output.json
```

### Test with Dashboard

1. Add to `.env`:
   ```bash
   SAGEMAKER_ENDPOINT_NAME=abs-risk-endpoint
   AWS_REGION=us-east-1
   ```

2. Start dashboard:
   ```bash
   ./start_dashboard.sh
   ```

3. Open browser: http://localhost:8050

4. Check logs for successful SageMaker connection

---

## Troubleshooting

### Endpoint Creation Failed

**Check CloudWatch Logs:**
```bash
aws logs describe-log-groups --log-group-name-prefix /aws/sagemaker/Endpoints
```

**Common Issues:**
- Insufficient IAM permissions
- Invalid model artifacts
- Resource limits exceeded

### Prediction Errors

**Issue:** `ModelError: An error occurred (ModelError) when calling the InvokeEndpoint operation`

**Solution:**
- Check model format matches inference.py expectations
- Verify feature dimensions match training data
- Check CloudWatch logs for detailed errors

### Timeout Issues

**Issue:** Endpoint takes too long to respond

**Solution:**
- Increase instance size: `ml.t2.large` or `ml.m5.large`
- Check model complexity
- Verify network connectivity

### Authentication Errors

**Issue:** `UnauthorizedOperation` or `AccessDenied`

**Solution:**
```bash
# Verify credentials
aws sts get-caller-identity

# Check IAM policies
aws iam list-attached-role-policies --role-name ABSolutionSageMakerRole
```

---

## Cost Estimation

### SageMaker Endpoint Costs (us-east-1)

| Instance Type | vCPUs | Memory | Price/Hour | Monthly (24/7) |
|---------------|-------|--------|------------|----------------|
| ml.t2.medium  | 2     | 4 GB   | $0.065     | ~$47           |
| ml.t2.large   | 2     | 8 GB   | $0.130     | ~$94           |
| ml.m5.large   | 2     | 8 GB   | $0.134     | ~$97           |
| ml.m5.xlarge  | 4     | 16 GB  | $0.269     | ~$195          |

### Additional Costs

- **S3 Storage:** ~$0.023/GB/month (minimal for model artifacts)
- **Data Transfer:** Free for same-region transfers
- **CloudWatch Logs:** ~$0.50/GB ingested

### Cost Optimization Tips

1. **Use Auto-scaling:** Scale down during low-traffic periods
2. **Scheduled Shutdowns:** Stop endpoint when not needed
3. **Use Spot Instances:** For non-production workloads
4. **Multi-Model Endpoints:** Host multiple models on same instance

### Delete Resources (Stop Billing)

```bash
# Delete endpoint
aws sagemaker delete-endpoint --endpoint-name abs-risk-endpoint

# Delete endpoint config
aws sagemaker delete-endpoint-config --endpoint-config-name abs-risk-config

# Delete model
aws sagemaker delete-model --model-name abs-risk-model

# Delete S3 bucket
aws s3 rb s3://absolution-sagemaker-models --force
```

---

## Next Steps

1. ✅ Deploy model to SageMaker
2. ✅ Configure dashboard with endpoint name
3. ✅ Test predictions
4. 🔄 Set up monitoring with CloudWatch
5. 🔄 Implement A/B testing with multiple model versions
6. 🔄 Set up CI/CD pipeline for model updates

---

## Support

For issues or questions:
- Check CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/
- AWS SageMaker Documentation: https://docs.aws.amazon.com/sagemaker/
- Project Issues: https://github.com/hongmf/ABSolution/issues

---

**Last Updated:** 2025-11-14
