# ABSolution

**AWS-Native Asset-Backed Securities Analytics Platform**

ABSolution is a comprehensive analytics platform for Asset-Backed Securities (ABS) that automatically downloads, processes, and analyzes SEC filings from major auto finance issuers. Built entirely on AWS serverless and AI services.

## Quick Start

Download SEC filings for Ford Credit, GM Financial, and Santander Consumer:

```bash
python src/sec_downloader/download_abs_filings.py --issuer all --limit 5
```

See [QUICKSTART.md](QUICKSTART.md) for detailed usage instructions.

## Features

### ✅ Implemented
- **SEC Filings Downloader** - Automatically download 10-K, 8-K, ABS-EE, and 10-D forms
- **Multi-Issuer Support** - Ford Credit, GM Financial, Santander Consumer
- **AWS Glue ETL** - Transform raw filings into normalized schema
- **Kinesis Streaming** - Real-time filing updates
- **Lambda Functions** - Risk scoring, normalization, and alerts
- **SageMaker Models** - Risk prediction and inference
- **Bedrock Integration** - AI-powered narrative generation
- **Benchmark API** - REST API for querying issuer benchmarks

### 🚧 In Progress
- Amazon Textract - Extract structured data from PDF exhibits
- Amazon Comprehend - NLP sentiment analysis on commentary
- QuickSight Dashboards - Interactive visualizations
- EventBridge Alerts - Automated risk threshold notifications

## Architecture

### Data Ingestion Layer
- **AWS Glue + DataBrew** - Automate ingestion and transformation of SEC filings
- **SEC Downloader** - Python tool to fetch filings from EDGAR
- **S3** - Raw and processed data storage

### Processing Layer
- **Amazon Textract** - Extract tables and forms from PDFs (10-D, 10-K)
- **Amazon Comprehend** - NLP for trend detection and sentiment analysis
- **AWS Glue** - ETL jobs for normalization

### Real-Time Pipeline
- **Amazon Kinesis** - Stream SEC filings as they're published
- **AWS Lambda** - Trigger normalization and scoring functions

### Analytics & AI
- **AWS SageMaker** - Predictive models for risk scoring and delinquency forecasting
- **Amazon Neptune** - Graph analytics for issuer/loan pool relationships
- **Amazon Bedrock** - Generate narrative insights

### Visualization & APIs
- **Amazon QuickSight** - Dynamic dashboards with drill-down comparisons
- **Benchmark API** - FastAPI endpoints for external queries
- **Amazon EventBridge** - Predictive alerts when risk thresholds breach

## Project Structure

```
ABSolution/
├── src/
│   ├── sec_downloader/          # SEC filings download tools
│   │   ├── download_abs_filings.py
│   │   ├── config.yaml
│   │   └── README.md
│   ├── glue/                    # AWS Glue ETL scripts
│   │   └── sec_filings_ingest.py
│   ├── kinesis/                 # Kinesis streaming
│   │   └── sec_filings_producer.py
│   ├── lambda/                  # Lambda functions
│   │   ├── filing_normalizer.py
│   │   ├── risk_scorer.py
│   │   └── alert_handler.py
│   ├── sagemaker/              # ML models
│   │   ├── train_risk_model.py
│   │   └── inference.py
│   ├── bedrock/                # AI narratives
│   │   └── narrative_generator.py
│   └── api/                    # REST API
│       └── benchmark_api.py
├── data/
│   └── sec_filings/            # Downloaded filings
├── tests/                      # Unit tests
├── requirements.txt
├── README.md
└── QUICKSTART.md
```

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download SEC Filings

```bash
# Download all issuers
python src/sec_downloader/download_abs_filings.py --issuer all

# Or specific issuer
python src/sec_downloader/download_abs_filings.py --issuer ford_credit
```

### 3. Upload to S3 (Optional)

```bash
python src/sec_downloader/download_abs_filings.py \
  --issuer all \
  --s3-bucket your-bucket \
  --s3-prefix raw-filings
```

### 4. Run AWS Glue ETL

```bash
aws glue start-job-run --job-name sec-filings-etl
```

### 5. Stream to Kinesis

```bash
python src/kinesis/sec_filings_producer.py --mode continuous
```

## Supported ABS Issuers

| Issuer | CIK | Asset Classes | Forms |
|--------|-----|---------------|-------|
| Ford Credit | 38777 | Auto Loans, Leases | 10-K, 8-K, ABS-EE, 10-D |
| GM Financial | 1576940 | Auto Loans, Leases | 10-K, 8-K, ABS-EE, 10-D |
| Santander Consumer | 1548429 | Auto Loans, Consumer Finance | 10-K, 8-K, ABS-EE, 10-D |

See `src/sec_downloader/config.yaml` for additional issuers.

## Key Differentiators

1. **End-to-End AWS Architecture** - Glue → S3 → SageMaker → QuickSight → Bedrock
2. **Serverless & Scalable** - Lambda, Kinesis, EventBridge
3. **AI-Powered Insights** - Bedrock narratives + QuickSight visualizations
4. **Real-Time Streaming** - Near real-time filing updates via Kinesis
5. **Predictive Alerts** - EventBridge triggers on risk threshold breaches
6. **Compliance Ready** - AWS Lake Formation for data governance

## Use Cases

- **ABS Investors** - Monitor portfolio risk and performance trends
- **Credit Analysts** - Track delinquency and FICO score changes
- **Risk Managers** - Predictive alerts for deteriorating credit quality
- **Research Teams** - Benchmark issuers and identify market trends
- **Compliance Officers** - Audit trail and SEC data handling compliance

## Documentation

- [Quick Start Guide](QUICKSTART.md) - Get up and running in 5 minutes
- [SEC Downloader](src/sec_downloader/README.md) - Detailed downloader documentation
- [API Documentation](src/api/README.md) - REST API reference
- [AWS Setup](docs/AWS_SETUP.md) - Cloud infrastructure deployment

## Development

### Run Tests

```bash
pytest tests/
```

### Lint

```bash
pylint src/
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

---

**Built for AWS-powered ABS analytics at scale** 🚀
