# ABSolution

# go beyond basic ETL -> use aws native services
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
