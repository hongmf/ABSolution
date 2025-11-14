#!/bin/bash

##############################################################################
# Quick SageMaker Deployment Script
# Automated deployment of ABSolution risk model to AWS SageMaker
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${CYAN}=========================================="
    echo -e "  $1"
    echo -e "==========================================${NC}"
    echo ""
}

# Banner
print_header "ABSolution SageMaker Deployment"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed."
    print_info "Install it with: pip install awscli"
    print_info "Or visit: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
print_info "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured or invalid."
    echo ""
    print_info "Configure AWS CLI with:"
    echo "  aws configure"
    echo ""
    print_info "You'll need:"
    echo "  - AWS Access Key ID"
    echo "  - AWS Secret Access Key"
    echo "  - Default region (e.g., us-east-1)"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

print_success "AWS credentials valid"
echo "  Account ID: $AWS_ACCOUNT"
echo "  Region: $AWS_REGION"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install required packages
print_info "Installing required packages..."
pip install boto3 sagemaker scikit-learn xgboost joblib --quiet
print_success "Packages installed"

# Prompt for deployment options
echo ""
print_header "Deployment Configuration"

echo "Select instance type for SageMaker endpoint:"
echo "  1) ml.t2.medium  - $0.065/hour (~$47/month) [Default]"
echo "  2) ml.t2.large   - $0.130/hour (~$94/month)"
echo "  3) ml.m5.large   - $0.134/hour (~$97/month)"
echo "  4) ml.m5.xlarge  - $0.269/hour (~$195/month)"
echo ""
read -p "Enter choice [1-4] (default: 1): " instance_choice

case $instance_choice in
    2)
        INSTANCE_TYPE="ml.t2.large"
        ;;
    3)
        INSTANCE_TYPE="ml.m5.large"
        ;;
    4)
        INSTANCE_TYPE="ml.m5.xlarge"
        ;;
    *)
        INSTANCE_TYPE="ml.t2.medium"
        ;;
esac

print_info "Selected instance type: $INSTANCE_TYPE"

# Endpoint name
echo ""
read -p "Enter endpoint name (default: abs-risk-endpoint): " ENDPOINT_NAME
ENDPOINT_NAME=${ENDPOINT_NAME:-abs-risk-endpoint}

print_info "Endpoint name: $ENDPOINT_NAME"

# Confirm deployment
echo ""
print_warning "This will create the following AWS resources:"
echo "  - IAM Role (if needed): ABSolutionSageMakerRole"
echo "  - S3 Bucket: absolution-sagemaker-$AWS_ACCOUNT-$AWS_REGION"
echo "  - SageMaker Model: abs-risk-model-<timestamp>"
echo "  - SageMaker Endpoint: $ENDPOINT_NAME"
echo "  - Instance Type: $INSTANCE_TYPE"
echo ""
echo "Estimated cost: See docs/SAGEMAKER_DEPLOYMENT.md for details"
echo ""

read -p "Continue with deployment? [y/N]: " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

# Run deployment
echo ""
print_header "Starting Deployment"

print_info "This will take 5-10 minutes..."
echo ""

python3 deploy_sagemaker.py \
    --region "$AWS_REGION" \
    --instance-type "$INSTANCE_TYPE" \
    --endpoint-name "$ENDPOINT_NAME"

# Check if deployment succeeded
if [ $? -eq 0 ]; then
    echo ""
    print_header "Deployment Successful!"

    print_success "SageMaker endpoint is ready!"
    echo ""
    print_info "Configuration for dashboard:"
    echo ""
    echo "Add these lines to your .env file:"
    echo "----------------------------------------"
    echo "SAGEMAKER_ENDPOINT_NAME=$ENDPOINT_NAME"
    echo "AWS_REGION=$AWS_REGION"
    echo "----------------------------------------"
    echo ""

    # Offer to create/update .env file
    read -p "Automatically update .env file? [Y/n]: " update_env

    if [[ ! $update_env =~ ^[Nn]$ ]]; then
        # Backup existing .env
        if [ -f ".env" ]; then
            cp .env .env.backup
            print_info "Backed up existing .env to .env.backup"
        fi

        # Update or create .env
        if [ -f ".env" ]; then
            # Update existing
            if grep -q "SAGEMAKER_ENDPOINT_NAME" .env; then
                sed -i "s/SAGEMAKER_ENDPOINT_NAME=.*/SAGEMAKER_ENDPOINT_NAME=$ENDPOINT_NAME/" .env
            else
                echo "SAGEMAKER_ENDPOINT_NAME=$ENDPOINT_NAME" >> .env
            fi

            if grep -q "AWS_REGION" .env; then
                sed -i "s/AWS_REGION=.*/AWS_REGION=$AWS_REGION/" .env
            else
                echo "AWS_REGION=$AWS_REGION" >> .env
            fi
        else
            # Create new
            cat > .env << EOF
# SageMaker Configuration
SAGEMAKER_ENDPOINT_NAME=$ENDPOINT_NAME
AWS_REGION=$AWS_REGION

# Dashboard Settings
PORT=8050
DEBUG=False
EOF
        fi

        print_success ".env file updated"
    fi

    echo ""
    print_info "Next steps:"
    echo "  1. Start the dashboard: ./start_dashboard.sh"
    echo "  2. Open browser: http://localhost:8050"
    echo "  3. View predictions in the Delinquencies panel"
    echo ""
    print_info "Deployment details saved to: sagemaker_deployment_info.json"
    echo ""

    # Offer to start dashboard
    read -p "Start the dashboard now? [Y/n]: " start_dash

    if [[ ! $start_dash =~ ^[Nn]$ ]]; then
        print_info "Starting dashboard..."
        ./start_dashboard.sh
    fi

else
    print_error "Deployment failed. Check the error messages above."
    exit 1
fi
