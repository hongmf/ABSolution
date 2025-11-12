# SEC Filings Downloader for ABS Issuers

This module downloads SEC filings for major Asset-Backed Securities (ABS) issuers including Ford Credit, GM Financial, and Santander Consumer.

## Overview

The downloader fetches ABS-related filings from the SEC EDGAR database and can optionally upload them to S3 for processing by the ABSolution analytics pipeline.

## Supported Issuers

### Primary Issuers
- **Ford Credit** (CIK: 38777) - Auto loans and leases
- **GM Financial** (CIK: 1576940) - Auto loans and leases
- **Santander Consumer** (CIK: 1548429) - Auto loans and consumer finance

### Form Types Downloaded
- **ABS-EE** - ABS Informational and Computational Material
- **10-D** - Asset-Backed Issuer Distribution Report (Monthly)
- **10-K** - Annual Report
- **8-K** - Current Report (Event-driven)
- **ABS-15G** - Asset-Backed Securities Report (Annual)

## Installation

Make sure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

## Usage

### Download filings for all issuers

```bash
python src/sec_downloader/download_abs_filings.py --issuer all
```

### Download for a specific issuer

```bash
# Ford Credit
python src/sec_downloader/download_abs_filings.py --issuer ford_credit

# GM Financial
python src/sec_downloader/download_abs_filings.py --issuer gm_financial

# Santander Consumer
python src/sec_downloader/download_abs_filings.py --issuer santander_consumer
```

### Download with date filter

```bash
# Download filings from the last 90 days
python src/sec_downloader/download_abs_filings.py \
  --issuer all \
  --after-date 2024-08-01
```

### Limit number of filings

```bash
# Download maximum 10 filings per form type
python src/sec_downloader/download_abs_filings.py \
  --issuer ford_credit \
  --limit 10
```

### Upload to S3

```bash
python src/sec_downloader/download_abs_filings.py \
  --issuer all \
  --s3-bucket absolution-sec-filings \
  --s3-prefix raw-filings
```

### Full example with all options

```bash
python src/sec_downloader/download_abs_filings.py \
  --issuer all \
  --after-date 2024-01-01 \
  --limit 50 \
  --download-dir ./data/sec_filings \
  --s3-bucket absolution-sec-filings \
  --s3-prefix raw-filings
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--issuer` | Which issuer to download (ford_credit, gm_financial, santander_consumer, all) | all |
| `--after-date` | Only download filings after this date (YYYY-MM-DD) | 1 year ago |
| `--limit` | Maximum number of filings per form type | No limit |
| `--download-dir` | Local directory to save filings | ./data/sec_filings |
| `--s3-bucket` | S3 bucket to upload filings (optional) | None |
| `--s3-prefix` | S3 prefix for uploaded filings | raw-filings |

## Output Structure

Downloaded filings are organized by issuer and form type:

```
data/sec_filings/
├── sec-edgar-filings/
│   ├── 38777/          # Ford Credit
│   │   ├── ABS-EE/
│   │   ├── 10-D/
│   │   ├── 10-K/
│   │   └── 8-K/
│   ├── 1576940/        # GM Financial
│   └── 1548429/        # Santander Consumer
├── Ford_Credit_summary.json
├── GM_Financial_summary.json
└── Santander_Consumer_summary.json
```

Each summary JSON file contains:
```json
{
  "issuer": "Ford Credit",
  "cik": "38777",
  "forms_downloaded": {
    "ABS-EE": 5,
    "10-D": 12,
    "10-K": 1,
    "8-K": 3
  },
  "total_downloads": 21,
  "errors": [],
  "download_date": "2025-11-12T10:30:00Z"
}
```

## Integration with ABSolution Pipeline

The downloaded filings integrate with the rest of the ABSolution pipeline:

1. **Download** → SEC filings are downloaded locally or to S3
2. **Ingest** → AWS Glue ETL (`src/glue/sec_filings_ingest.py`) processes the raw filings
3. **Extract** → Amazon Textract extracts structured data from PDFs
4. **Analyze** → Amazon Comprehend performs NLP and sentiment analysis
5. **Stream** → Kinesis streams real-time updates (`src/kinesis/sec_filings_producer.py`)
6. **Score** → Lambda functions calculate risk scores (`src/lambda/risk_scorer.py`)
7. **Alert** → EventBridge triggers alerts for threshold breaches
8. **Visualize** → QuickSight dashboards and Bedrock narrative insights

## SEC EDGAR API Compliance

This downloader follows SEC EDGAR API best practices:
- Includes proper User-Agent header with contact information
- Respects rate limits (10 requests per second)
- Uses official sec-edgar-downloader library
- Implements retry logic for failed requests

## Configuration

Edit `config.yaml` to:
- Add new issuers
- Modify filing types
- Change download settings
- Configure S3 settings

## Examples

### Quick start - Download last 30 days for Ford Credit
```bash
python src/sec_downloader/download_abs_filings.py \
  --issuer ford_credit \
  --after-date $(date -d '30 days ago' +%Y-%m-%d)
```

### Production - Download all issuers to S3
```bash
python src/sec_downloader/download_abs_filings.py \
  --issuer all \
  --after-date 2024-01-01 \
  --s3-bucket absolution-sec-filings \
  --s3-prefix production/raw-filings
```

### Testing - Download limited sample
```bash
python src/sec_downloader/download_abs_filings.py \
  --issuer gm_financial \
  --limit 5 \
  --download-dir ./test_data
```

## Troubleshooting

### Rate Limiting
If you encounter rate limiting errors, the downloader will automatically retry with exponential backoff.

### Network Errors
Check your internet connection and SEC EDGAR API status: https://www.sec.gov/edgar/sec-api-documentation

### S3 Upload Errors
Ensure your AWS credentials are configured:
```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

## Next Steps

After downloading filings:
1. Run AWS Glue ETL job to process and normalize the data
2. Set up Kinesis stream for real-time monitoring
3. Configure Lambda functions for risk scoring
4. Create QuickSight dashboards for visualization

See main project README for full pipeline setup instructions.
