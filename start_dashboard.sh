#!/bin/bash

##############################################################################
# ABSolution Dashboard Startup Script
# Launches the interactive analytics dashboard with SageMaker predictions
##############################################################################

set -e  # Exit on error

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Banner
echo "=========================================="
echo "   ABSolution Analytics Dashboard"
echo "   AWS-Native ABS Analytics Platform"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_info "Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
print_info "Checking dependencies..."
if [ -f "requirements-dashboard.txt" ]; then
    print_info "Installing dashboard dependencies from requirements-dashboard.txt..."
    pip install --upgrade pip --quiet
    pip install -r requirements-dashboard.txt --quiet
    print_success "Dependencies installed"
elif [ -f "requirements.txt" ]; then
    print_warning "Using full requirements.txt (this may take a while)..."
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    print_success "Dependencies installed"
else
    print_warning "No requirements file found. Installing essential packages..."
    pip install dash plotly pandas numpy boto3 --quiet
    print_success "Essential packages installed"
fi

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    print_info "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
    print_success "Environment variables loaded"
else
    print_warning ".env file not found. Using default configuration."
    print_info "You can create a .env file with the following variables:"
    echo "  - SAGEMAKER_ENDPOINT_NAME: Name of your SageMaker endpoint"
    echo "  - AWS_REGION: AWS region (default: us-east-1)"
    echo "  - PORT: Dashboard port (default: 8050)"
    echo "  - DEBUG: Enable debug mode (default: False)"
fi

# Set default environment variables if not set
export AWS_REGION=${AWS_REGION:-us-east-1}
export PORT=${PORT:-8050}
export DEBUG=${DEBUG:-False}

# Display configuration
echo ""
print_info "Dashboard Configuration:"
echo "  Port: $PORT"
echo "  AWS Region: $AWS_REGION"
echo "  Debug Mode: $DEBUG"
if [ -n "$SAGEMAKER_ENDPOINT_NAME" ]; then
    echo "  SageMaker Endpoint: $SAGEMAKER_ENDPOINT_NAME"
    print_success "SageMaker endpoint configured - using ML predictions"
else
    echo "  SageMaker Endpoint: Not configured"
    print_warning "No SageMaker endpoint - using local prediction model"
fi
echo ""

# Check AWS credentials
print_info "Checking AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    print_success "AWS credentials valid (Account: $AWS_ACCOUNT)"
else
    print_warning "AWS credentials not configured or invalid"
    print_info "Dashboard will use local prediction model"
    print_info "To use SageMaker predictions, configure AWS credentials:"
    echo "  - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
    echo "  - Or configure AWS CLI: aws configure"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the dashboard
print_info "Starting ABSolution Dashboard..."
echo ""
print_success "=========================================="
print_success "Dashboard is starting!"
print_success "=========================================="
echo ""
print_info "Access the dashboard at:"
echo ""
echo "  🌐 http://localhost:$PORT"
echo ""
print_info "Press Ctrl+C to stop the dashboard"
echo ""

# Add Python path
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Start the dashboard
python3 "$SCRIPT_DIR/src/dashboard/app.py" 2>&1 | tee logs/dashboard_$(date +%Y%m%d_%H%M%S).log
