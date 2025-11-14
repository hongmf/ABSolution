# ABSolution Streamlit UI

A comprehensive web-based user interface for the ABSolution AWS-Native ABS Analytics Platform, built with Streamlit.

## Features

### 📋 Data Panel
The Data Panel provides comprehensive filtering and exploration capabilities for SEC ABS filing data:

- **Advanced Filters**:
  - **Date Range**: Quick select (Last 30/90 days, 6 months, 1 year) or custom date range
  - **Asset Class**: Filter by AUTO_LOAN, CREDIT_CARD, STUDENT_LOAN, MORTGAGE, and more
  - **Form Type**: Filter by ABS-EE, 10-D, 10-K, 8-K forms
  - **Company**: Select specific issuers by company name and CIK

- **Data Summary**:
  - Total filings count
  - Number of unique companies
  - Asset class diversity
  - Total pool balance across all filings
  - Average 90+ day delinquency rate

- **Visualizations**:
  - Filings distribution by asset class (pie chart)
  - Filings by form type (bar chart)
  - Filing trends over time (line chart)

- **Interactive Data Table**:
  - View detailed filing information
  - Formatted financial metrics
  - Sortable columns
  - Export to CSV functionality

### 📈 Analytics Panel
The Analytics Panel offers deep insights with multiple analysis views:

#### 1. Performance Metrics
- **Key Performance Indicators**:
  - Average delinquency rates (30, 60, 90+ days)
  - Cumulative default rates
  - Loss rates

- **Delinquency Analysis**:
  - Delinquency cascade visualization
  - Distribution histograms
  - Trend analysis

- **Credit Quality Metrics**:
  - FICO score statistics and distribution
  - Loan-to-Value (LTV) ratio analysis
  - Debt-to-Income (DTI) ratio metrics

- **Pool Balance Analysis**:
  - Total balance by asset class
  - Top 10 companies by pool balance

#### 2. Risk Analytics
- **Risk Score Overview**:
  - Average risk scores
  - High-risk entity count
  - Risk component breakdown (delinquency, default, liquidity)

- **Risk Distribution**:
  - Risk level categorization (LOW, MEDIUM, HIGH, CRITICAL)
  - Risk score histograms
  - Risk by asset class comparison

- **Performance-Based Risk Indicators**:
  - High delinquency rate entities
  - Delinquency vs FICO correlation
  - Default rate distribution

#### 3. Comparative Analysis
- **Asset Class Comparison**:
  - Side-by-side metric comparison
  - Statistical summaries (mean, median, std dev)
  - Multi-metric visualization

- **Company Benchmarking**:
  - Top 10 companies heatmap
  - Key metrics comparison
  - Performance rankings

#### 4. Trend Analysis
- **Time Series Analysis**:
  - Configurable aggregation periods (Daily, Weekly, Monthly, Quarterly)
  - Delinquency trends over time
  - Default rate trends
  - FICO score evolution

- **Multi-Metric Comparison**:
  - Normalized metric trends
  - Correlation analysis
  - Asset class-specific trends

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- (Optional) AWS credentials for live data

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install UI dependencies specifically:

```bash
pip install streamlit plotly altair matplotlib seaborn pandas numpy scikit-learn
```

## Running the UI

### Quick Start

Use the provided shell script:

```bash
chmod +x run_ui.sh
./run_ui.sh
```

### Manual Start

```bash
streamlit run app.py
```

The UI will be available at `http://localhost:8501`

## Data Modes

### Mock Data Mode (Default)
The UI includes a comprehensive mock data generator that creates realistic ABS filing data for testing and demonstration purposes.

- Generates data for multiple companies across different asset classes
- Includes realistic performance metrics, delinquency rates, and credit scores
- Useful for testing and demonstrations without AWS credentials

### AWS Data Mode
Connect to live AWS services (DynamoDB, S3) to analyze real ABS filing data.

Requirements:
- AWS credentials configured (`~/.aws/credentials` or environment variables)
- DynamoDB tables: `abs-filings`, `abs-risk-scores`
- S3 bucket access for processed data

Toggle between modes using the "Use Mock Data" checkbox in the sidebar.

## Project Structure

```
ABSolution/
├── app.py                          # Main Streamlit application
├── run_ui.sh                       # Quick start script
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── src/
│   └── ui/
│       ├── __init__.py
│       ├── data_loader.py          # Data loading utilities
│       └── pages/
│           ├── __init__.py
│           ├── data_panel.py       # Data exploration panel
│           └── analytics_panel.py  # Analytics dashboard
└── requirements.txt                # Python dependencies
```

## Configuration

### Streamlit Configuration
Edit `.streamlit/config.toml` to customize:
- Theme colors
- Server settings
- Browser behavior

### AWS Configuration
Set environment variables or update `data_loader.py`:
- `FILINGS_TABLE`: DynamoDB table for filings (default: `abs-filings`)
- `RISK_TABLE`: DynamoDB table for risk scores (default: `abs-risk-scores`)
- `PROCESSED_BUCKET`: S3 bucket for processed data (default: `abs-solution-processed-data`)

## Features in Detail

### Caching
The UI implements Streamlit's caching mechanism for optimal performance:
- Data is cached for 5 minutes (300 seconds)
- Metadata (companies, asset classes) cached for 10 minutes
- Manual cache refresh available in sidebar

### Responsive Design
- Wide layout for maximum screen utilization
- Responsive columns for different screen sizes
- Mobile-friendly interface

### Interactive Visualizations
Built with Plotly for rich, interactive charts:
- Zoom and pan capabilities
- Hover tooltips with detailed information
- Download charts as images
- Full-screen mode

### Export Capabilities
- Download filtered data as CSV
- Include all fields in export
- Timestamp in filename for organization

## Tips for Use

1. **Start with Data Panel**: Familiarize yourself with available data using filters
2. **Use Quick Selects**: Leverage preset date ranges for common analysis periods
3. **Export Data**: Download filtered datasets for offline analysis
4. **Refresh Regularly**: Click "Refresh Data" to clear cache and get latest data
5. **Combine Filters**: Use multiple filters together for targeted analysis
6. **Explore All Analytics Views**: Each view offers unique insights

## Troubleshooting

### Import Errors
If you encounter import errors:
```bash
pip install --upgrade streamlit plotly pandas
```

### AWS Connection Issues
- Verify AWS credentials: `aws configure`
- Check IAM permissions for DynamoDB and S3
- Enable "Use Mock Data" mode for testing

### Port Already in Use
If port 8501 is busy:
```bash
streamlit run app.py --server.port 8502
```

### Cache Issues
Clear Streamlit cache:
```bash
streamlit cache clear
```

## Development

### Adding New Visualizations
1. Edit `src/ui/pages/analytics_panel.py`
2. Add new render functions
3. Update analytics type selector

### Modifying Filters
1. Edit `src/ui/pages/data_panel.py`
2. Update filter section
3. Pass new filters to data loader

### Extending Data Sources
1. Edit `src/ui/data_loader.py`
2. Add new data loading methods
3. Update caching decorators

## Performance Optimization

- Data is cached to minimize AWS API calls
- Use date range filters to limit data volume
- Asset class and form type filters applied server-side
- Pagination for large datasets

## Security Notes

- AWS credentials should never be committed to version control
- Use IAM roles with minimal required permissions
- Enable AWS CloudTrail for audit logging
- Implement VPC endpoints for private AWS access

## Integration with ABSolution Platform

The UI integrates with the full ABSolution platform:
- **AWS Glue**: Displays normalized filing data
- **Lambda Functions**: Shows processed filing results
- **DynamoDB**: Queries filing and risk score tables
- **SageMaker**: Displays ML-generated risk scores
- **Bedrock**: (Future) AI-generated narrative insights

## Future Enhancements

- [ ] AI-powered narrative insights using Amazon Bedrock
- [ ] Real-time updates via WebSocket
- [ ] Advanced filtering with saved filter sets
- [ ] Custom dashboard builder
- [ ] Alert configuration and management
- [ ] Multi-user authentication
- [ ] Role-based access control
- [ ] Export to Excel with formatted reports
- [ ] Scheduled report generation
- [ ] API endpoint explorer

## Support

For issues or questions:
1. Check AWS service status
2. Review CloudWatch logs
3. Verify data availability in DynamoDB
4. Test with mock data mode first

## License

Part of the ABSolution project - AWS-Native ABS Analytics Platform
