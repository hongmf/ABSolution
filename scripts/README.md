# ABSolution Scripts

Utility scripts for managing SEC filings and AWS S3 operations.

## Available Scripts

### 1. `upload_to_s3.py` - Upload SEC Filings to S3

Upload downloaded SEC filings to AWS S3 bucket.

**Usage:**
```bash
# Upload all downloaded filings
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --directory data/sec_filings

# Dry run (see what would be uploaded)
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --directory data/sec_filings \
  --dry-run

# Upload and verify
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --directory data/sec_filings \
  --list

# Just list what's already in S3
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --list-only
```

**Options:**
- `--bucket` - S3 bucket name (required)
- `--directory` - Local directory to upload (default: data/sec_filings)
- `--prefix` - S3 prefix/folder (default: raw-filings)
- `--dry-run` - Preview without uploading
- `--list` - List files after upload
- `--list-only` - Only list S3 files

### 2. `check_s3.sh` - Verify S3 Uploads

Quick verification of SEC filings in S3.

**Usage:**
```bash
# Check default bucket
./scripts/check_s3.sh

# Check specific bucket
./scripts/check_s3.sh my-bucket-name

# Check specific bucket and prefix
./scripts/check_s3.sh my-bucket-name custom-prefix
```

**What it checks:**
- ✓ Bucket accessibility
- ✓ Files by issuer (Ford Credit, GM Financial, Santander Consumer)
- ✓ Overall statistics (total files, total size)
- ✓ Recent files
- ✓ Files by form type (10-K, 8-K, ABS-EE, etc.)

**Example output:**
```
═══════════════════════════════════════════════════════════════
  SEC Filings S3 Status Check
═══════════════════════════════════════════════════════════════

Bucket: s3://absolution-sec-filings
Prefix: raw-filings

Checking bucket access...
✓ Bucket accessible

═══════════════════════════════════════════════════════════════
  File Count by Issuer
═══════════════════════════════════════════════════════════════
✓ Ford Credit (CIK: 0000038777): 4 files
✓ GM Financial (CIK: 0001576940): 4 files
  Santander Consumer (CIK: 0001548429): 0 files

═══════════════════════════════════════════════════════════════
  Overall Statistics
═══════════════════════════════════════════════════════════════
Total Objects: 8
   Total Size: 160.5 MiB
```

## Prerequisites

### AWS Credentials

Configure AWS credentials before using these scripts:

```bash
# Option 1: AWS CLI configure
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

# Option 3: AWS credentials file (~/.aws/credentials)
[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key
```

### Create S3 Bucket

```bash
# Create bucket
aws s3 mb s3://absolution-sec-filings --region us-east-1

# Verify
aws s3 ls s3://absolution-sec-filings/
```

## Complete Workflow

### 1. Download SEC Filings

```bash
python src/sec_downloader/download_abs_filings.py --issuer all --limit 5
```

### 2. Upload to S3

```bash
# Preview first
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --dry-run

# Then upload
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --list
```

### 3. Verify Upload

```bash
./scripts/check_s3.sh absolution-sec-filings
```

### 4. Trigger AWS Glue ETL

```bash
aws glue start-job-run \
  --job-name sec-filings-etl \
  --arguments '{"--S3_INPUT_PATH":"s3://absolution-sec-filings/raw-filings/"}'
```

## Advanced Usage

### Upload Specific Issuers Only

```bash
# Upload only Ford Credit files
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --directory data/sec_filings/sec-edgar-filings/0000038777 \
  --prefix raw-filings/sec-edgar-filings/0000038777
```

### Upload with Custom Prefix

```bash
# Organize by date
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --prefix raw-filings/2025-11-12
```

### Batch Upload Multiple Directories

```bash
#!/bin/bash
for cik in "0000038777" "0001576940" "0001548429"; do
  python scripts/upload_to_s3.py \
    --bucket absolution-sec-filings \
    --directory data/sec_filings/sec-edgar-filings/$cik \
    --prefix raw-filings/sec-edgar-filings/$cik
done
```

## Integration with AWS Services

### Trigger Lambda on Upload

Set up S3 event notifications to trigger Lambda when files are uploaded:

```bash
aws s3api put-bucket-notification-configuration \
  --bucket absolution-sec-filings \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [{
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:123456789:function:filing_normalizer",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [{
            "Name": "prefix",
            "Value": "raw-filings/"
          }]
        }
      }
    }]
  }'
```

### Configure Glue Crawler

Automatically catalog uploaded files:

```bash
aws glue create-crawler \
  --name sec-filings-crawler \
  --database-name absolution \
  --role AWSGlueServiceRole \
  --targets "S3Targets=[{Path=s3://absolution-sec-filings/raw-filings/}]"

aws glue start-crawler --name sec-filings-crawler
```

## Troubleshooting

### Permission Errors

```bash
# Check your IAM user
aws iam get-user

# Check S3 permissions
aws s3api get-bucket-acl --bucket absolution-sec-filings
```

### Upload Failures

```bash
# Check if files exist locally
ls -lh data/sec_filings/sec-edgar-filings/

# Try uploading a single file
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --directory data/sec_filings \
  --dry-run
```

### Slow Uploads

```bash
# Configure AWS CLI for faster uploads
aws configure set default.s3.max_concurrent_requests 20
aws configure set default.s3.multipart_threshold 64MB
aws configure set default.s3.multipart_chunksize 16MB
```

## See Also

- [S3 Upload Guide](../docs/S3_UPLOAD_GUIDE.md) - Comprehensive S3 documentation
- [SEC Downloader](../src/sec_downloader/README.md) - Download SEC filings
- [Quick Start](../QUICKSTART.md) - Get started quickly

---

**Scripts ready to power your AWS SEC filings pipeline!** 🚀
