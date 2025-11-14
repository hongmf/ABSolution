#!/bin/bash
#
# Start the ABSolution Analytics Dashboard
# This script launches the Panel dashboard for visualizing ABS analytics data
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ABSolution Analytics Dashboard Launcher${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not found.${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}\n"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if requirements are installed
echo -e "${GREEN}Checking dependencies...${NC}"
if ! python -c "import panel" 2>/dev/null; then
    echo -e "${YELLOW}Installing required packages...${NC}\n"
    pip install -r requirements.txt
fi

# Parse command line arguments
USE_SAMPLE_DATA=false
PORT=5006
REGION="us-east-1"
SAVE_HTML=""
NO_BROWSER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --sample-data)
            USE_SAMPLE_DATA=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --save-html)
            SAVE_HTML="--save-html $2"
            shift 2
            ;;
        --no-browser)
            NO_BROWSER="--no-browser"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --sample-data         Use sample data instead of DynamoDB"
            echo "  --port PORT           Port to serve dashboard on (default: 5006)"
            echo "  --region REGION       AWS region (default: us-east-1)"
            echo "  --save-html FILE      Save dashboard to HTML file instead of serving"
            echo "  --no-browser          Don't open browser automatically"
            echo "  -h, --help            Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command
CMD="python -m src.visualization.dashboard --region $REGION --port $PORT"

if [ "$USE_SAMPLE_DATA" = true ]; then
    CMD="$CMD --sample-data"
    echo -e "${YELLOW}Using sample data (not connecting to DynamoDB)${NC}\n"
fi

if [ -n "$SAVE_HTML" ]; then
    CMD="$CMD $SAVE_HTML"
    echo -e "${GREEN}Saving dashboard to HTML file${NC}\n"
else
    echo -e "${GREEN}Starting dashboard server...${NC}"
    echo -e "${GREEN}Dashboard will be available at: ${YELLOW}http://localhost:$PORT${NC}\n"
fi

if [ -n "$NO_BROWSER" ]; then
    CMD="$CMD $NO_BROWSER"
fi

# Run the dashboard
echo -e "${GREEN}Launching dashboard...${NC}\n"
echo "Command: $CMD"
echo ""

eval $CMD
