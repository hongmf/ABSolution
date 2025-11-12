#!/bin/bash

# ABSolution AWS Configuration Script
# This script helps you set up AWS credentials and environment

set -e

echo "=========================================="
echo "  ABSolution AWS Configuration Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

print_info() {
    echo -e "  $1"
}

# Check if AWS CLI is installed
echo "Checking prerequisites..."
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed"
    echo ""
    echo "Please install AWS CLI first:"
    echo "  Linux: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html"
    echo "  macOS: brew install awscli"
    echo "  Windows: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-windows.html"
    exit 1
fi
print_success "AWS CLI is installed ($(aws --version))"

# Configure AWS credentials
echo ""
echo "=========================================="
echo "  Step 1: Configure AWS Credentials"
echo "=========================================="
echo ""

if [ -f ~/.aws/credentials ]; then
    print_warning "AWS credentials already configured"
    read -p "Do you want to reconfigure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping AWS credentials configuration"
    else
        aws configure
    fi
else
    print_info "Please enter your AWS credentials"
    aws configure
fi

# Verify AWS credentials
echo ""
echo "Verifying AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    print_success "AWS credentials are valid"

    # Get account details
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
    AWS_REGION=$(aws configure get region)

    echo ""
    print_info "Account ID: $AWS_ACCOUNT_ID"
    print_info "User ARN: $AWS_USER_ARN"
    print_info "Region: $AWS_REGION"
else
    print_error "AWS credentials are invalid"
    exit 1
fi

# Configure environment file
echo ""
echo "=========================================="
echo "  Step 2: Configure Environment File"
echo "=========================================="
echo ""

if [ -f .env ]; then
    print_warning ".env file already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Keeping existing .env file"
        ENV_UPDATED=false
    else
        ENV_UPDATED=true
    fi
else
    ENV_UPDATED=true
fi

if [ "$ENV_UPDATED" = true ]; then
    # Copy from example
    cp .env.example .env

    # Update with actual values
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/AWS_ACCOUNT_ID=.*/AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID/" .env
        sed -i '' "s/AWS_REGION=.*/AWS_REGION=$AWS_REGION/" .env
    else
        # Linux
        sed -i "s/AWS_ACCOUNT_ID=.*/AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID/" .env
        sed -i "s/AWS_REGION=.*/AWS_REGION=$AWS_REGION/" .env
    fi

    # Update bucket names with actual account ID
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/123456789012/$AWS_ACCOUNT_ID/g" .env
    else
        sed -i "s/123456789012/$AWS_ACCOUNT_ID/g" .env
    fi

    print_success ".env file created and configured"

    # Ask for alert email
    echo ""
    read -p "Enter your email for alerts (press Enter to skip): " ALERT_EMAIL
    if [ ! -z "$ALERT_EMAIL" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/ALERT_EMAIL=.*/ALERT_EMAIL=$ALERT_EMAIL/" .env
        else
            sed -i "s/ALERT_EMAIL=.*/ALERT_EMAIL=$ALERT_EMAIL/" .env
        fi
        print_success "Alert email configured: $ALERT_EMAIL"
    fi
fi

# Check required permissions
echo ""
echo "=========================================="
echo "  Step 3: Verify IAM Permissions"
echo "=========================================="
echo ""

print_info "Checking required IAM permissions..."

# Check CloudFormation permissions
if aws cloudformation describe-stacks --max-items 1 &> /dev/null || [[ $? -eq 254 ]]; then
    print_success "CloudFormation: ✓"
else
    print_error "CloudFormation: ✗ (Missing permissions)"
fi

# Check S3 permissions
if aws s3 ls &> /dev/null; then
    print_success "S3: ✓"
else
    print_error "S3: ✗ (Missing permissions)"
fi

# Check Lambda permissions
if aws lambda list-functions --max-items 1 &> /dev/null; then
    print_success "Lambda: ✓"
else
    print_error "Lambda: ✗ (Missing permissions)"
fi

# Check DynamoDB permissions
if aws dynamodb list-tables --max-items 1 &> /dev/null; then
    print_success "DynamoDB: ✓"
else
    print_error "DynamoDB: ✗ (Missing permissions)"
fi

# Summary
echo ""
echo "=========================================="
echo "  Configuration Summary"
echo "=========================================="
echo ""
print_success "AWS credentials configured"
print_success "Environment file ready (.env)"
print_success "Region: $AWS_REGION"
print_success "Account: $AWS_ACCOUNT_ID"

echo ""
echo "Next steps:"
echo "  1. Review and edit .env file if needed"
echo "  2. Run deployment: bash scripts/deploy_all.sh"
echo "  3. Or deploy CloudFormation stack: npm run deploy:stack"
echo ""
print_success "Configuration complete!"
