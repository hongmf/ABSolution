# ABSolution - Quick Start Guide

## SEC Filings Downloader for ABS Issuers

### ✅ What's Been Built

A comprehensive SEC filings downloader for major auto finance companies:

- **Ford Credit** (CIK: 38777)
- **GM Financial** (CIK: 1576940)
- **Santander Consumer** (CIK: 1548429)

### 📊 Current Status

The downloader successfully retrieves:
- **10-K** forms (Annual Reports) - ✅ Working
- **8-K** forms (Current Reports) - ✅ Working
- **ABS-EE** forms (ABS Computational Material)
- **10-D** forms (Asset-Backed Distribution Reports)
- **ABS-15G** forms (ABS Reports)

**Test Results:**
- Ford Credit: 4 filings downloaded (2 x 10-K, 2 x 8-K)
- GM Financial: 4 filings downloaded (2 x 10-K, 2 x 8-K)
- Total: 8 filings (~160MB of data)

### 🚀 Quick Start

#### 1. Download filings for all issuers

```bash
python src/sec_downloader/download_abs_filings.py --issuer all --limit 5
```

#### 2. Download for a specific company

```bash
# Ford Credit
python src/sec_downloader/download_abs_filings.py --issuer ford_credit

# GM Financial
python src/sec_downloader/download_abs_filings.py --issuer gm_financial

# Santander Consumer
python src/sec_downloader/download_abs_filings.py --issuer santander_consumer
```

#### 3. Download recent filings only

```bash
# Last 90 days
python src/sec_downloader/download_abs_filings.py \
  --issuer all \
  --after-date $(date -d '90 days ago' +%Y-%m-%d)
```

#### 4. Upload to S3 for AWS processing

```bash
python src/sec_downloader/download_abs_filings.py \
  --issuer all \
  --s3-bucket your-bucket-name \
  --s3-prefix raw-filings
```

### 📁 Output Structure

```
data/sec_filings/
├── sec-edgar-filings/
│   ├── 0000038777/          # Ford Credit
│   │   ├── 10-K/
│   │   │   └── 0000038777-25-000238/
│   │   │       └── full-submission.txt
│   │   └── 8-K/
│   ├── 0001576940/          # GM Financial
│   └── 0001548429/          # Santander Consumer
├── Ford_Credit_summary.json
├── GM_Financial_summary.json
└── Santander_Consumer_summary.json
```

### 📝 Sample Output

Each summary JSON contains:
```json
{
  "issuer": "Ford Credit",
  "cik": "38777",
  "forms_downloaded": {
    "ABS-EE": 0,
    "10-D": 0,
    "10-K": 2,
    "8-K": 2
  },
  "total_downloads": 4,
  "errors": [],
  "download_date": "2025-11-12T06:19:05.704342"
}
```

### 🔄 Next Steps

Once you have the filings downloaded, you can:

1. **Process with AWS Glue** - Normalize and transform the data
   ```bash
   # Run the Glue ETL job (requires AWS setup)
   aws glue start-job-run --job-name sec-filings-etl
   ```

2. **Stream to Kinesis** - For real-time monitoring
   ```bash
   python src/kinesis/sec_filings_producer.py --mode continuous
   ```

3. **Extract PDF data** - Using Amazon Textract
4. **Analyze sentiment** - Using Amazon Comprehend
5. **Generate insights** - Using Amazon Bedrock

### 🛠️ Advanced Usage

#### Custom date ranges

```bash
python src/sec_downloader/download_abs_filings.py \
  --issuer ford_credit \
  --after-date 2024-01-01 \
  --before-date 2024-12-31
```

#### Production deployment

```bash
# Download all filings since 2020 and upload to S3
python src/sec_downloader/download_abs_filings.py \
  --issuer all \
  --after-date 2020-01-01 \
  --s3-bucket absolution-sec-filings \
  --s3-prefix production/raw-filings
```

### 📚 Documentation

- Full documentation: `src/sec_downloader/README.md`
- Configuration: `src/sec_downloader/config.yaml`
- Main project: `README.md`

### 🔍 What Makes This Special

1. **AWS-Native** - Designed to integrate with AWS Glue, Textract, Comprehend
2. **Automated** - One command downloads all filings for multiple issuers
3. **Structured** - Organized by issuer, form type, and date
4. **Tracked** - JSON summaries for each download session
5. **Scalable** - Can upload directly to S3 for cloud processing
6. **Compliant** - Follows SEC EDGAR API best practices

### 🎯 Project Vision

ABSolution is an **AWS-native ABS Analytics Platform** that:

- ✅ **Downloads** SEC filings automatically
- ⏳ **Ingests** with AWS Glue for ETL
- ⏳ **Extracts** structured data with Textract
- ⏳ **Analyzes** sentiment with Comprehend
- ⏳ **Streams** real-time updates with Kinesis
- ⏳ **Scores** risk with Lambda functions
- ⏳ **Predicts** with SageMaker models
- ⏳ **Visualizes** with QuickSight dashboards
- ⏳ **Narrates** insights with Bedrock AI

### 🤝 Contributing

Edit `src/sec_downloader/config.yaml` to add more ABS issuers:

```yaml
additional_issuers:
  ally_financial:
    cik: "40729"
    name: "Ally Financial"
  capital_one:
    cik: "927628"
    name: "Capital One"
```

---

**Ready to analyze ABS data at scale!** 🚀
