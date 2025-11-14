#!/bin/bash

# Setup script for CDK infrastructure
# Run this before deploying

set -e

echo "Setting up ABSolution CDK Infrastructure..."
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo "Install from: https://nodejs.org/"
    exit 1
fi
echo "✓ Node.js installed: $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed"
    exit 1
fi
echo "✓ npm installed: $(npm --version)"

# Install CDK globally if not present
if ! command -v cdk &> /dev/null; then
    echo ""
    echo "Installing AWS CDK globally..."
    npm install -g aws-cdk
fi
echo "✓ AWS CDK installed: $(cdk --version)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✓ Python 3 installed: $(python3 --version)"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo ""
    echo "⚠️  AWS CLI is not installed"
    echo "Install from: https://aws.amazon.com/cli/"
    exit 1
fi
echo "✓ AWS CLI installed: $(aws --version)"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo ""
    echo "⚠️  AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi
echo "✓ AWS credentials configured"

# Set environment variables
export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION=${AWS_REGION:-us-east-1}

echo ""
echo "✓ Setup complete!"
echo ""
echo "Environment:"
echo "  Account: $CDK_DEFAULT_ACCOUNT"
echo "  Region: $CDK_DEFAULT_REGION"
echo ""
echo "Next steps:"
echo "  1. cdk bootstrap (first time only)"
echo "  2. cdk synth (to see CloudFormation template)"
echo "  3. cdk deploy ABSolutionMultiAgentStack"
echo ""
