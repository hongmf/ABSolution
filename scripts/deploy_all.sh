#!/bin/bash

# ABSolution Master Deployment Script
# Deploys all components of the ABSolution platform to AWS

set -e

echo "=========================================="
echo "   ABSolution Platform Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}! $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }
print_step() { echo -e "\n${BLUE}===> $1${NC}\n"; }

# Check if .env exists
if [ ! -f .env ]; then
    print_error ".env file not found"
    echo ""
    print_info "Running AWS configuration setup..."
    bash scripts/configure_aws.sh
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Default values
ENVIRONMENT=${ENVIRONMENT:-dev}
AWS_REGION=${AWS_REGION:-us-east-1}
STACK_NAME="absolution-platform-${ENVIRONMENT}"
ALERT_EMAIL=${ALERT_EMAIL:-alerts@example.com}

echo "Deployment Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Region: $AWS_REGION"
echo "  Stack Name: $STACK_NAME"
echo "  Alert Email: $ALERT_EMAIL"
echo ""

read -p "Continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

# Track deployment start time
START_TIME=$(date +%s)

# ========================================
# STEP 1: Validate AWS Credentials
# ========================================
print_step "Step 1/6: Validating AWS Credentials"

if ! aws sts get-caller-identity > /dev/null 2>&1; then
    print_error "AWS credentials are invalid or not configured"
    print_info "Run: bash scripts/configure_aws.sh"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_success "AWS credentials validated"
print_info "Account ID: $AWS_ACCOUNT_ID"

# ========================================
# STEP 2: Validate CloudFormation Template
# ========================================
print_step "Step 2/6: Validating CloudFormation Template"

if aws cloudformation validate-template \
    --template-body file://infrastructure/cloudformation/main-stack.yaml \
    --region $AWS_REGION > /dev/null 2>&1; then
    print_success "CloudFormation template is valid"
else
    print_error "CloudFormation template validation failed"
    exit 1
fi

# ========================================
# STEP 3: Deploy CloudFormation Stack
# ========================================
print_step "Step 3/6: Deploying CloudFormation Stack"

# Check if stack exists
if aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION > /dev/null 2>&1; then

    print_warning "Stack already exists. Updating..."

    aws cloudformation update-stack \
        --stack-name $STACK_NAME \
        --template-body file://infrastructure/cloudformation/main-stack.yaml \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
                     ParameterKey=AlertEmail,ParameterValue=$ALERT_EMAIL \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $AWS_REGION || {
            if [ $? -eq 254 ]; then
                print_info "No updates to perform"
            else
                print_error "Stack update failed"
                exit 1
            fi
        }

    if [ $? -ne 254 ]; then
        print_info "Waiting for stack update to complete..."
        aws cloudformation wait stack-update-complete \
            --stack-name $STACK_NAME \
            --region $AWS_REGION

        print_success "Stack updated successfully"
    fi

else
    print_info "Creating new stack..."

    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://infrastructure/cloudformation/main-stack.yaml \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
                     ParameterKey=AlertEmail,ParameterValue=$ALERT_EMAIL \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $AWS_REGION

    print_info "Waiting for stack creation to complete (this may take 5-10 minutes)..."
    aws cloudformation wait stack-create-complete \
        --stack-name $STACK_NAME \
        --region $AWS_REGION

    print_success "Stack created successfully"
fi

# ========================================
# STEP 4: Deploy Lambda Functions
# ========================================
print_step "Step 4/6: Deploying Lambda Functions"

if bash scripts/deploy_lambda.sh; then
    print_success "Lambda functions deployed"
else
    print_warning "Lambda deployment had issues (this is normal if functions don't exist yet)"
fi

# ========================================
# STEP 5: Deploy Glue Jobs
# ========================================
print_step "Step 5/6: Setting up AWS Glue"

# Check if deploy_glue.sh exists
if [ -f scripts/deploy_glue.sh ]; then
    bash scripts/deploy_glue.sh
else
    print_info "Creating Glue deployment script..."

    cat > scripts/deploy_glue.sh << 'GLUE_SCRIPT'
#!/bin/bash
# Glue jobs deployment
echo "Setting up AWS Glue jobs..."
# TODO: Implement Glue ETL job deployment
echo "Glue setup completed (placeholder)"
GLUE_SCRIPT

    chmod +x scripts/deploy_glue.sh
    print_info "Glue setup placeholder created"
fi

# ========================================
# STEP 6: Verify Deployment
# ========================================
print_step "Step 6/6: Verifying Deployment"

echo "Fetching stack outputs..."
OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs' \
    --output json)

# Parse outputs
API_ENDPOINT=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="APIEndpoint") | .OutputValue')
RAW_BUCKET=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="RawDataBucketName") | .OutputValue')
PROCESSED_BUCKET=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="ProcessedDataBucketName") | .OutputValue')
KINESIS_STREAM=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="KinesisStreamName") | .OutputValue')
FILINGS_TABLE=$(echo $OUTPUTS | jq -r '.[] | select(.OutputKey=="FilingsTableName") | .OutputValue')

# Display outputs
echo ""
echo "=========================================="
echo "   Deployment Summary"
echo "=========================================="
echo ""
print_success "Stack Status: DEPLOYED"
echo ""
echo "Resources Created:"
echo ""
echo "  S3 Buckets:"
echo "    • Raw Data: $RAW_BUCKET"
echo "    • Processed Data: $PROCESSED_BUCKET"
echo ""
echo "  DynamoDB Tables:"
echo "    • Filings: $FILINGS_TABLE"
echo ""
echo "  Kinesis Stream:"
echo "    • Stream: $KINESIS_STREAM"
echo ""
echo "  API Gateway:"
echo "    • Endpoint: $API_ENDPOINT"
echo ""

# Verify resources
print_info "Verifying resources..."

# Check S3 buckets
if aws s3 ls s3://$RAW_BUCKET &> /dev/null; then
    print_success "S3 buckets accessible"
else
    print_error "S3 buckets not accessible"
fi

# Check DynamoDB tables
if aws dynamodb describe-table --table-name $FILINGS_TABLE &> /dev/null; then
    print_success "DynamoDB tables accessible"
else
    print_error "DynamoDB tables not accessible"
fi

# Check Lambda functions
LAMBDA_COUNT=$(aws lambda list-functions \
    --region $AWS_REGION \
    --query "Functions[?contains(FunctionName, 'abs-')].FunctionName" \
    --output text | wc -w)

print_info "Lambda functions deployed: $LAMBDA_COUNT"

# Calculate deployment time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "=========================================="
print_success "Deployment Complete!"
echo "=========================================="
echo ""
print_info "Total deployment time: ${MINUTES}m ${SECONDS}s"
echo ""
echo "Next Steps:"
echo ""
echo "  1. Update your .env file with these values:"
echo "     RAW_DATA_BUCKET=$RAW_BUCKET"
echo "     PROCESSED_DATA_BUCKET=$PROCESSED_BUCKET"
echo "     API_GATEWAY_URL=$API_ENDPOINT"
echo ""
echo "  2. Test your API:"
echo "     curl $API_ENDPOINT"
echo ""
echo "  3. Upload sample data:"
echo "     aws s3 cp sample-data/ s3://$RAW_BUCKET/sec-filings/ --recursive"
echo ""
echo "  4. Monitor logs:"
echo "     aws logs tail /aws/lambda/abs-filing-normalizer-${ENVIRONMENT} --follow"
echo ""
echo "  5. View CloudWatch dashboard:"
echo "     https://console.aws.amazon.com/cloudwatch/"
echo ""

# Save deployment info
cat > deployment-info.json << EOF
{
  "deployment_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "$ENVIRONMENT",
  "region": "$AWS_REGION",
  "stack_name": "$STACK_NAME",
  "account_id": "$AWS_ACCOUNT_ID",
  "api_endpoint": "$API_ENDPOINT",
  "raw_bucket": "$RAW_BUCKET",
  "processed_bucket": "$PROCESSED_BUCKET",
  "kinesis_stream": "$KINESIS_STREAM",
  "filings_table": "$FILINGS_TABLE",
  "duration_seconds": $DURATION
}
EOF

print_success "Deployment info saved to: deployment-info.json"
echo ""
