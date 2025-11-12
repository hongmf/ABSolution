# S3 Upload Quick Reference

## 🚀 Quick Start (3 Steps)

### Step 1: Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region: us-east-1
```

### Step 2: Create S3 Bucket (if needed)
```bash
aws s3 mb s3://absolution-sec-filings --region us-east-1
```

### Step 3: Upload Your Files
```bash
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --directory data/sec_filings \
  --list
```

## 📊 Verify Upload

```bash
# Quick check with our tool
./scripts/check_s3.sh absolution-sec-filings

# Or using AWS CLI
aws s3 ls s3://absolution-sec-filings/raw-filings/ --recursive --human-readable
```

## 🎯 Common Commands

### Preview Before Upload (Dry Run)
```bash
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --dry-run
```

### Upload with Custom Path
```bash
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --prefix production/filings-2025
```

### Just List What's in S3
```bash
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --list-only
```

### Download from S3
```bash
aws s3 sync s3://absolution-sec-filings/raw-filings/ ./local-backup/
```

## 📁 Expected S3 Structure

After upload, your bucket will look like:

```
s3://absolution-sec-filings/
└── raw-filings/
    └── sec-edgar-filings/
        ├── 0000038777/           # Ford Credit
        │   ├── 10-K/
        │   │   ├── 0000038777-25-000238/
        │   │   │   └── full-submission.txt (26 MB)
        │   │   └── 0000038777-24-000206/
        │   │       └── full-submission.txt (23 MB)
        │   └── 8-K/
        │       └── ...
        ├── 0001576940/           # GM Financial
        │   └── ...
        └── 0001548429/           # Santander Consumer
            └── ...
```

## ✅ Success Indicators

After upload, you should see:

1. **Upload Script Output:**
   ```
   ✓ Uploaded: sec-edgar-filings/0000038777/10-K/... (26,000,000 bytes)
   ✓ Uploaded: sec-edgar-filings/0000038777/8-K/... (15,000,000 bytes)

   UPLOAD SUMMARY
   ================================================================================
     Uploaded:  8 files
     Failed:    0 files
     Total size: 160.50 MB
   ```

2. **Verification Output:**
   ```
   ✓ Ford Credit (CIK: 0000038777): 4 files
   ✓ GM Financial (CIK: 1576940): 4 files

   Total Objects: 8
      Total Size: 160.5 MiB
   ```

## 🔗 Next Steps After Upload

### 1. Configure AWS Glue to Process Files
```bash
aws glue start-job-run \
  --job-name sec-filings-etl \
  --arguments '{
    "--S3_INPUT_PATH":"s3://absolution-sec-filings/raw-filings/",
    "--S3_OUTPUT_PATH":"s3://absolution-sec-filings/processed/"
  }'
```

### 2. Set Up S3 Event Notifications
Trigger Lambda when new files arrive:
```bash
aws s3api put-bucket-notification-configuration \
  --bucket absolution-sec-filings \
  --notification-configuration file://s3-notifications.json
```

### 3. Create Athena Tables
Query files directly:
```sql
CREATE EXTERNAL TABLE sec_filings (
  cik STRING,
  form_type STRING,
  filing_date DATE,
  content STRING
)
STORED AS TEXTFILE
LOCATION 's3://absolution-sec-filings/raw-filings/';
```

## 🛠️ Troubleshooting

### "Access Denied" Error
```bash
# Check credentials
aws sts get-caller-identity

# Check bucket permissions
aws s3api get-bucket-acl --bucket absolution-sec-filings
```

### Upload Stuck/Slow
```bash
# Configure for faster uploads
aws configure set default.s3.max_concurrent_requests 20
aws configure set default.s3.multipart_threshold 64MB
```

### Files Not Showing Up
```bash
# Refresh and check again
aws s3 ls s3://absolution-sec-filings/raw-filings/ --recursive | grep "full-submission"

# Check CloudWatch if using Lambda
aws logs tail /aws/lambda/filing_normalizer
```

## 📚 Documentation

- **Full Guide:** [docs/S3_UPLOAD_GUIDE.md](docs/S3_UPLOAD_GUIDE.md)
- **Scripts:** [scripts/README.md](scripts/README.md)
- **Downloader:** [src/sec_downloader/README.md](src/sec_downloader/README.md)

## 💡 Pro Tips

1. **Always dry-run first** to preview uploads
2. **Use --list flag** to verify uploads immediately
3. **Check costs** with `aws s3 ls --summarize`
4. **Set up lifecycle policies** to archive old filings to Glacier
5. **Enable versioning** for production buckets

---

**Your SEC filings are ready for cloud-powered analytics!** ☁️
