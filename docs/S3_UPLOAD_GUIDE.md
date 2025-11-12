# S3 Upload Guide for SEC Filings

This guide shows you how to upload downloaded SEC filings to AWS S3 and verify the uploads.

## Prerequisites

1. **AWS Credentials Configured**
   ```bash
   # Option 1: AWS CLI configure
   aws configure

   # Option 2: Environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

2. **S3 Bucket Created**
   ```bash
   # Create bucket if it doesn't exist
   aws s3 mb s3://absolution-sec-filings --region us-east-1
   ```

3. **Verify Access**
   ```bash
   # Check you can access the bucket
   aws s3 ls s3://absolution-sec-filings/
   ```

## Method 1: Download and Upload in One Command

The easiest way - the downloader automatically uploads to S3 as it downloads:

```bash
python src/sec_downloader/download_abs_filings.py \
  --issuer all \
  --limit 5 \
  --s3-bucket absolution-sec-filings \
  --s3-prefix raw-filings
```

### Example Output
```
2025-11-12 06:17:47 - INFO - Downloading filings for: Ford Credit
2025-11-12 06:18:35 - INFO - Downloaded 4 filings
2025-11-12 06:18:36 - INFO - Uploading filings to S3: s3://absolution-sec-filings/raw-filings/
2025-11-12 06:18:45 - INFO - Uploaded 4 files to S3
```

## Method 2: Upload Existing Downloads

If you've already downloaded files locally, use the standalone upload script:

```bash
# Upload all downloaded filings
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --directory data/sec_filings \
  --prefix raw-filings
```

### Dry Run First
```bash
# See what would be uploaded without actually uploading
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --directory data/sec_filings \
  --dry-run
```

### Upload with Verification
```bash
# Upload and then list files to verify
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --directory data/sec_filings \
  --list
```

## Method 3: Using AWS CLI Directly

For more control, use the AWS CLI:

```bash
# Upload entire directory
aws s3 cp data/sec_filings/ \
  s3://absolution-sec-filings/raw-filings/ \
  --recursive

# Upload with progress
aws s3 sync data/sec_filings/ \
  s3://absolution-sec-filings/raw-filings/

# Upload with custom metadata
aws s3 cp data/sec_filings/ \
  s3://absolution-sec-filings/raw-filings/ \
  --recursive \
  --metadata "source=sec-edgar,pipeline=absolution"
```

## Verify Uploads

### Option 1: Using the Upload Script
```bash
python scripts/upload_to_s3.py \
  --bucket absolution-sec-filings \
  --list-only
```

### Option 2: Using AWS CLI
```bash
# List all files
aws s3 ls s3://absolution-sec-filings/raw-filings/ --recursive

# Count files
aws s3 ls s3://absolution-sec-filings/raw-filings/ --recursive | wc -l

# Show total size
aws s3 ls s3://absolution-sec-filings/raw-filings/ --recursive --human-readable --summarize

# List files for specific issuer
aws s3 ls s3://absolution-sec-filings/raw-filings/sec-edgar-filings/0000038777/ --recursive
```

### Option 3: Using boto3 Python Script
```python
import boto3

s3 = boto3.client('s3')
response = s3.list_objects_v2(
    Bucket='absolution-sec-filings',
    Prefix='raw-filings/'
)

for obj in response.get('Contents', []):
    print(f"{obj['Key']} - {obj['Size']/1024/1024:.2f} MB")
```

## Expected S3 Structure

After uploading, your S3 bucket should look like this:

```
s3://absolution-sec-filings/
└── raw-filings/
    └── sec-edgar-filings/
        ├── 0000038777/              # Ford Credit (CIK)
        │   ├── 10-K/
        │   │   ├── 0000038777-25-000238/
        │   │   │   └── full-submission.txt
        │   │   └── 0000038777-24-000206/
        │   │       └── full-submission.txt
        │   └── 8-K/
        │       ├── 0000038777-25-000189/
        │       │   └── full-submission.txt
        │       └── 0000038777-25-000234/
        │           └── full-submission.txt
        ├── 0001576940/              # GM Financial
        │   ├── 10-K/
        │   └── 8-K/
        └── 0001548429/              # Santander Consumer
            ├── 10-K/
            └── 8-K/
```

## Download Files from S3

If you need to download files later:

```bash
# Download specific file
aws s3 cp s3://absolution-sec-filings/raw-filings/sec-edgar-filings/0000038777/10-K/0000038777-25-000238/full-submission.txt \
  ./local-file.txt

# Download entire directory
aws s3 sync s3://absolution-sec-filings/raw-filings/ \
  ./data/sec_filings/

# Download with exclusions
aws s3 sync s3://absolution-sec-filings/raw-filings/ \
  ./data/sec_filings/ \
  --exclude "*" \
  --include "*/10-K/*"
```

## S3 Bucket Configuration

### Recommended Bucket Policy

Create a bucket policy for the Glue job to access the files:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::absolution-sec-filings",
        "arn:aws:s3:::absolution-sec-filings/*"
      ]
    }
  ]
}
```

### Lifecycle Policy

Automatically archive old filings to Glacier:

```json
{
  "Rules": [
    {
      "Id": "ArchiveOldFilings",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 365,
          "StorageClass": "GLACIER"
        }
      ],
      "Filter": {
        "Prefix": "raw-filings/"
      }
    }
  ]
}
```

Apply it:
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket absolution-sec-filings \
  --lifecycle-configuration file://lifecycle-policy.json
```

## Integration with AWS Glue

Once files are in S3, configure your Glue job to read from there:

```python
# In your Glue job
S3_INPUT_PATH = "s3://absolution-sec-filings/raw-filings/sec-edgar-filings/"
S3_OUTPUT_PATH = "s3://absolution-sec-filings/processed-filings/"

# Read from S3
dynamic_frame = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [S3_INPUT_PATH]},
    format="json"
)
```

## Monitoring and Costs

### Check S3 Storage Costs
```bash
# Get bucket size
aws s3 ls s3://absolution-sec-filings --recursive --summarize | tail -2

# Get detailed metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name BucketSizeBytes \
  --dimensions Name=BucketName,Value=absolution-sec-filings \
  --start-time 2025-11-01T00:00:00Z \
  --end-time 2025-11-12T23:59:59Z \
  --period 86400 \
  --statistics Average
```

### Enable S3 Event Notifications

Trigger Lambda when new files are uploaded:

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

## Troubleshooting

### Permission Denied
```bash
# Check your IAM permissions
aws iam get-user

# Check bucket policy
aws s3api get-bucket-policy --bucket absolution-sec-filings
```

### Files Not Appearing
```bash
# Check if upload actually completed
aws s3 ls s3://absolution-sec-filings/raw-filings/ --recursive | grep "full-submission.txt"

# Check CloudWatch logs if using Lambda
aws logs tail /aws/lambda/filing_normalizer --follow
```

### Upload Too Slow
```bash
# Use multipart upload for large files (handled automatically)
# Or use AWS CLI sync with multiple threads
aws configure set default.s3.max_concurrent_requests 20
```

## Next Steps

After uploading to S3:

1. **Configure Glue Crawler** to catalog the data
2. **Set up Kinesis** to stream new filings
3. **Configure Lambda** to trigger on new uploads
4. **Create Athena queries** to analyze the data
5. **Build QuickSight dashboards** for visualization

See [AWS_SETUP.md](AWS_SETUP.md) for full infrastructure deployment.

---

**Your SEC filings are now in the cloud and ready for AWS-powered analytics!** ☁️
