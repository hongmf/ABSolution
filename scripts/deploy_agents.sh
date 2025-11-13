#!/bin/bash

# ABSolution Multi-Agent System Deployment Script
# This script deploys the complete multi-agent infrastructure to AWS

set -e  # Exit on error

echo "==========================================="
echo "ABSolution Multi-Agent System Deployment"
echo "==========================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI installed${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials configured${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 installed${NC}"

# Check Node.js (for CDK)
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js installed${NC}"

# Check CDK
if ! command -v cdk &> /dev/null; then
    echo -e "${YELLOW}Installing AWS CDK...${NC}"
    npm install -g aws-cdk
fi
echo -e "${GREEN}✓ AWS CDK installed${NC}"

echo ""
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

echo ""
echo -e "${YELLOW}Installing CDK dependencies...${NC}"
cd infrastructure
pip install -r requirements.txt 2>/dev/null || pip install aws-cdk-lib constructs
cd ..

# Get AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo ""
echo -e "${GREEN}Deploying to:${NC}"
echo "  Account: $AWS_ACCOUNT"
echo "  Region: $AWS_REGION"
echo ""

# Confirm deployment
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Bootstrap CDK (if not already done)
echo ""
echo -e "${YELLOW}Bootstrapping CDK environment...${NC}"
cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION || true

# Package Lambda functions
echo ""
echo -e "${YELLOW}Packaging Lambda functions...${NC}"
cd src/agents
mkdir -p ../../build/lambda
zip -r ../../build/lambda/agents.zip . -x "*.pyc" "__pycache__/*" "*.git*"
cd ../..

# Deploy infrastructure
echo ""
echo -e "${YELLOW}Deploying infrastructure stack...${NC}"
cd infrastructure
cdk deploy MultiAgentStack --require-approval never

# Get outputs
echo ""
echo -e "${GREEN}Deployment successful!${NC}"
echo ""
echo "Getting stack outputs..."
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name MultiAgentStack \
    --query 'Stacks[0].Outputs[?OutputKey==`DialogueAPIEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "Not available")

echo ""
echo -e "${GREEN}==========================================="
echo "Deployment Complete!"
echo "===========================================${NC}"
echo ""
echo "API Endpoint: $API_ENDPOINT"
echo ""
echo "Next steps:"
echo "1. Enable Bedrock models in AWS Console:"
echo "   https://console.aws.amazon.com/bedrock/home?region=$AWS_REGION#/models"
echo ""
echo "2. Deploy SageMaker risk model:"
echo "   python src/sagemaker/train_risk_model.py"
echo "   python src/sagemaker/inference.py --deploy"
echo ""
echo "3. Test the API:"
echo "   curl -X POST $API_ENDPOINT/session"
echo ""
echo "4. View documentation:"
echo "   docs/multi_agent_system.md"
echo ""

cd ..
