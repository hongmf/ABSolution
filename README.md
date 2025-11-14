# ABSolution

**AWS-Native Asset-Backed Securities Analytics Platform**

<<<<<<< HEAD
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
=======
A comprehensive, AI-powered platform for analyzing Asset-Backed Securities (ABS) using AWS services, featuring a multi-agent AI system for intelligent analysis and insights.

## 🤖 Multi-Agent AI System

ABSolution features a sophisticated multi-agent AI system powered by Amazon Bedrock. Five specialized agents work together to provide comprehensive ABS analysis:

- **Data Analyst Agent** - Queries and analyzes SEC filings
- **Risk Assessor Agent** - Evaluates credit risk with ML models
- **Report Generator Agent** - Creates narrative reports
- **Benchmark Analyst Agent** - Performs comparative analysis
- **Alert Monitor Agent** - Detects anomalies and generates alerts

**Quick Start:**
```bash
# Deploy the multi-agent system
./scripts/deploy_agents.sh

# Start the web UI
python3 scripts/serve_ui.py

# Open browser and navigate to http://localhost:8080
```

📖 **Documentation:**
- [Multi-Agent System](docs/multi_agent_system.md) - Complete technical documentation
- [Dialogue Panel Guide](docs/dialogue_panel_guide.md) - User interface guide

## 🌐 Dialogue Panel

Access the multi-agent system through a beautiful web interface:

![Dialogue Panel Features](https://img.shields.io/badge/UI-Modern_Dark_Theme-blue)
![Real-time](https://img.shields.io/badge/Updates-Real--time-green)
![Responsive](https://img.shields.io/badge/Design-Responsive-purple)

**Features:**
- 💬 Natural chat interface
- 🤖 Real-time agent status indicators
- 💡 AI-generated follow-up suggestions
- 📊 Agent attribution for transparency
- 💾 Export conversations as Markdown
- ⚡ Quick action buttons
- 📱 Responsive mobile design

**Try it:**
```bash
python3 scripts/serve_ui.py
# Open http://localhost:8080
```

## Architecture Overview

### go beyond basic ETL -> use aws native services
- AWS glue + glue databrew
  automate ingestion and transformation of sec filings into a normalized schema
- amazon textract
  extract structured data from pdfs in filings (10-D, 10-K, etc) with high accuracy
- amazon comprehend
  apply nlp to detect trends, anomalies and sentiment in issuercommentary section
# run time data pipeline
- amazon kinesis
  stream sec filings as they are published for near real-time updates
- aws lambda
  trigger normalization and scoring functions automatically when new filings arrive
# advanced analytics and AI
- aws sagemaker
  build predictive models for issue risk scoring and delinquency forecasting
- graph analytics with Amazon Neptune
  model relationships between issuers, loan pools, and performance metrics for deeper insights.
# Interactive dashboard with AI insights
- **Interactive Panel Dashboard**
  web-based dashboard with all plots and visualizations displayed in an organized panel layout
  - Risk score distribution with threshold alerts
  - Delinquency trends with moving averages
  - Asset class performance comparisons
  - Top high-risk issuers
  - Risk timeline with alerts
  - Launch with: `./scripts/start_dashboard.sh --sample-data`
- **Amazon QuickSight**
  create dynamic dashboards with drill-down comparisons (programmatic setup included)
- **Generative AI Layer**
  use Amazon Bedrock to generate narrative insights like: "Issue X shows tightening credit standards with rising FICO averages, while Issuer Y exhibits increasing delinquency trends."
# compliance and security edge
- AWS Lake Formation
  security manage access to normalize ABS data
- Audit Trail
  show how your solution ensures compliance with SEC data handling standards
# "Wow Factor" features
- Voice-enabled insights
  Integrate Alexa for Business to qery ABS trends verbally
- Predictive alerts:
  use Amazon Eventbridge to trigger alerts when risk thresholds are breached.
- Benchmark API
  expose an API for external teams to query issuer benchmarks
# Hackathon differentiator
- End-to-end architecture on AWS (Glue -> S3 -> Sagemaker -> QuickSight -> Bedrock)
- Scalable and serverless
  Lambda, Kinesis, EventBridge
- AI-powered Narrative + visualization
  Bedrock + QuickSight + Interactive Panel Dashboard
- real-time streaming + predictive alerts
<<<<<<< HEAD
>>>>>>> 51a0f88c9bb6b22029bf9ca97630fa86daa24c50
=======

## Quick Start - Visualization Dashboard

**View all plots in an interactive panel:**

```bash
# Install dependencies
pip install -r requirements.txt

# Launch dashboard with sample data (no AWS credentials needed)
./scripts/start_dashboard.sh --sample-data

# Or launch with live DynamoDB data
./scripts/start_dashboard.sh --region us-east-1
```

The dashboard will open at `http://localhost:5006` with all plots displayed in organized tabs:
- **Overview**: Key metrics dashboard
- **Risk Analysis**: Risk scores and timelines
- **Asset Classes**: Performance by asset type
- **Issuers**: Issuer-specific analysis
- **Delinquencies**: Delinquency tracking

See [src/visualization/README.md](src/visualization/README.md) for detailed documentation.
>>>>>>> 9a6ab352210a0e14c82125e5f3a6ac4920f05553
