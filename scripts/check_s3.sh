#!/bin/bash
# Quick S3 verification script for SEC filings

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BUCKET="${1:-absolution-sec-filings}"
PREFIX="${2:-raw-filings}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  SEC Filings S3 Status Check${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Bucket:${NC} s3://$BUCKET"
echo -e "${YELLOW}Prefix:${NC} $PREFIX"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI not installed${NC}"
    echo "Install it with: pip install awscli"
    exit 1
fi

# Check if bucket exists
echo -e "${BLUE}Checking bucket access...${NC}"
if aws s3 ls "s3://$BUCKET" &> /dev/null; then
    echo -e "${GREEN}✓ Bucket accessible${NC}"
else
    echo -e "${RED}✗ Cannot access bucket${NC}"
    echo "Please check:"
    echo "  1. Bucket name is correct"
    echo "  2. AWS credentials are configured (run: aws configure)"
    echo "  3. You have s3:ListBucket permission"
    exit 1
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  File Count by Issuer${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Count files for each issuer
for cik in "0000038777" "0001576940" "0001548429"; do
    case $cik in
        "0000038777")
            issuer="Ford Credit"
            ;;
        "0001576940")
            issuer="GM Financial"
            ;;
        "0001548429")
            issuer="Santander Consumer"
            ;;
    esac

    count=$(aws s3 ls "s3://$BUCKET/$PREFIX/sec-edgar-filings/$cik/" --recursive 2>/dev/null | wc -l || echo "0")

    if [ "$count" -gt 0 ]; then
        echo -e "${GREEN}✓ $issuer (CIK: $cik): $count files${NC}"
    else
        echo -e "${YELLOW}  $issuer (CIK: $cik): $count files${NC}"
    fi
done

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Overall Statistics${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Get total statistics
aws s3 ls "s3://$BUCKET/$PREFIX/" --recursive --summarize --human-readable 2>/dev/null | tail -2

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Recent Files (Latest 10)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

aws s3 ls "s3://$BUCKET/$PREFIX/sec-edgar-filings/" --recursive | sort -k1,2 -r | head -10

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  File Types${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Count by form type
for form in "10-K" "8-K" "ABS-EE" "10-D" "ABS-15G"; do
    count=$(aws s3 ls "s3://$BUCKET/$PREFIX/sec-edgar-filings/" --recursive 2>/dev/null | grep "/$form/" | wc -l || echo "0")
    if [ "$count" -gt 0 ]; then
        echo -e "${GREEN}  $form: $count files${NC}"
    else
        echo -e "${YELLOW}  $form: $count files${NC}"
    fi
done

echo ""
echo -e "${GREEN}✓ S3 check complete!${NC}"
echo ""
echo "To view all files, run:"
echo "  aws s3 ls s3://$BUCKET/$PREFIX/ --recursive"
echo ""
echo "To download files, run:"
echo "  aws s3 sync s3://$BUCKET/$PREFIX/ ./local-directory/"
echo ""
