#!/bin/bash

# ABSolution Lambda Deployment Script
# Packages and deploys all Lambda functions

set -e

echo "=========================================="
echo "  ABSolution Lambda Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "  $1"; }

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    print_success "Environment loaded from .env"
else
    print_error ".env file not found"
    echo "Run: bash scripts/configure_aws.sh first"
    exit 1
fi

# Default values
ENVIRONMENT=${ENVIRONMENT:-dev}
AWS_REGION=${AWS_REGION:-us-east-1}

# Create temporary build directory
BUILD_DIR="./build/lambda"
mkdir -p $BUILD_DIR

echo ""
echo "Packaging Lambda functions..."
echo ""

# Function to package and deploy a Lambda function
package_and_deploy() {
    local FUNCTION_NAME=$1
    local SOURCE_DIR=$2
    local HANDLER=$3

    echo "Processing: $FUNCTION_NAME"

    # Create package directory
    PACKAGE_DIR="$BUILD_DIR/$FUNCTION_NAME"
    mkdir -p $PACKAGE_DIR

    # Copy source code
    if [ -f "$SOURCE_DIR" ]; then
        cp $SOURCE_DIR $PACKAGE_DIR/
        print_success "  Source copied"
    else
        print_error "  Source file not found: $SOURCE_DIR"
        return 1
    fi

    # Copy shared utilities if they exist
    if [ -d "src/lambda/shared" ]; then
        cp -r src/lambda/shared $PACKAGE_DIR/ 2>/dev/null || true
    fi

    # Install dependencies if requirements.txt exists
    if [ -f "src/lambda/requirements.txt" ]; then
        print_info "  Installing dependencies..."
        pip install -r src/lambda/requirements.txt -t $PACKAGE_DIR/ --quiet
        print_success "  Dependencies installed"
    fi

    # Create deployment package
    cd $PACKAGE_DIR
    ZIP_FILE="../${FUNCTION_NAME}.zip"
    zip -r $ZIP_FILE . -q
    cd - > /dev/null

    print_success "  Package created: ${FUNCTION_NAME}.zip"

    # Update Lambda function
    FULL_FUNCTION_NAME="${FUNCTION_NAME}-${ENVIRONMENT}"

    print_info "  Updating Lambda function: $FULL_FUNCTION_NAME"

    if aws lambda update-function-code \
        --function-name $FULL_FUNCTION_NAME \
        --zip-file fileb://${BUILD_DIR}/${FUNCTION_NAME}.zip \
        --region $AWS_REGION > /dev/null 2>&1; then
        print_success "  Deployed: $FULL_FUNCTION_NAME"
    else
        print_error "  Failed to deploy: $FULL_FUNCTION_NAME"
        print_info "  Note: Function may not exist yet (created by CloudFormation)"
    fi

    echo ""
}

# Deploy each Lambda function
if [ -d "src/lambda" ]; then
    # Filing Normalizer
    if [ -f "src/lambda/filing_normalizer.py" ]; then
        package_and_deploy "abs-filing-normalizer" \
                           "src/lambda/filing_normalizer.py" \
                           "filing_normalizer.lambda_handler"
    fi

    # Risk Scorer
    if [ -f "src/lambda/risk_scorer.py" ]; then
        package_and_deploy "abs-risk-scorer" \
                           "src/lambda/risk_scorer.py" \
                           "risk_scorer.lambda_handler"
    fi

    # Alert Handler
    if [ -f "src/lambda/alert_handler.py" ]; then
        package_and_deploy "abs-alert-handler" \
                           "src/lambda/alert_handler.py" \
                           "alert_handler.lambda_handler"
    fi

    # Benchmark API
    if [ -f "src/lambda/benchmark_api.py" ]; then
        package_and_deploy "abs-benchmark-api" \
                           "src/lambda/benchmark_api.py" \
                           "benchmark_api.lambda_handler"
    fi
else
    print_error "Lambda source directory not found: src/lambda"
    echo ""
    print_info "Creating placeholder Lambda functions..."
    mkdir -p src/lambda

    # Create placeholder functions if they don't exist
    cat > src/lambda/filing_normalizer.py << 'EOF'
import json
import os
import boto3
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Normalize SEC filings data
    """
    print(f"Received event: {json.dumps(event)}")

    # TODO: Implement filing normalization logic
    # 1. Extract data from S3
    # 2. Normalize format
    # 3. Store in DynamoDB
    # 4. Put in processed bucket

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Filing normalizer executed',
            'timestamp': datetime.now().isoformat()
        })
    }
EOF

    cat > src/lambda/risk_scorer.py << 'EOF'
import json
import os
import boto3
from datetime import datetime

sagemaker_runtime = boto3.client('sagemaker-runtime')
dynamodb = boto3.resource('dynamodb')
events = boto3.client('events')

def lambda_handler(event, context):
    """
    Score risk using SageMaker model
    """
    print(f"Received event: {json.dumps(event)}")

    # TODO: Implement risk scoring logic
    # 1. Get filing data
    # 2. Invoke SageMaker endpoint
    # 3. Store risk score
    # 4. Trigger alerts if threshold exceeded

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Risk scorer executed',
            'timestamp': datetime.now().isoformat()
        })
    }
EOF

    cat > src/lambda/alert_handler.py << 'EOF'
import json
import os
import boto3
from datetime import datetime

sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Handle risk alerts
    """
    print(f"Received event: {json.dumps(event)}")

    # TODO: Implement alert handling logic
    # 1. Process alert event
    # 2. Store in DynamoDB
    # 3. Send SNS notification

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Alert handler executed',
            'timestamp': datetime.now().isoformat()
        })
    }
EOF

    cat > src/lambda/benchmark_api.py << 'EOF'
import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Benchmark API endpoint
    """
    print(f"Received event: {json.dumps(event)}")

    # Parse request
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    path = event.get('rawPath', '/')

    # TODO: Implement API logic
    # 1. Query DynamoDB for benchmark data
    # 2. Filter and aggregate results
    # 3. Return formatted response

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Benchmark API',
            'path': path,
            'method': http_method,
            'timestamp': datetime.now().isoformat()
        })
    }
EOF

    print_success "Placeholder Lambda functions created"
    echo ""
fi

# Cleanup
echo "Cleaning up..."
# Keep the build directory for inspection
# rm -rf $BUILD_DIR
print_success "Build artifacts saved in: $BUILD_DIR"

echo ""
echo "=========================================="
print_success "Lambda deployment complete!"
echo "=========================================="
echo ""
print_info "Note: Lambda functions must be created by CloudFormation first"
print_info "Run: npm run deploy:stack (if not already done)"
