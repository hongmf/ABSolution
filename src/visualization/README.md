# ABSolution Visualization Module

This module provides comprehensive visualization and dashboard capabilities for the ABSolution ABS Analytics Platform.

## Features

- **Interactive Panel Dashboard**: Web-based dashboard with all ABS analytics plots
- **Plotly Visualizations**: Interactive plots for risk scores, delinquency trends, asset classes, and issuers
- **QuickSight Integration**: Programmatic creation of AWS QuickSight dashboards
- **Sample Data Generation**: Built-in sample data for testing and demonstration
- **DynamoDB Integration**: Load real data from DynamoDB tables

## Components

### 1. Plot Utilities (`plot_utils.py`)

Functions to create various plots:

- `create_risk_score_distribution()` - Histogram of risk scores
- `create_delinquency_trends()` - Time series of delinquency rates
- `create_asset_class_comparison()` - Comparison across asset classes
- `create_issuer_performance()` - Multi-metric issuer dashboard
- `create_risk_timeline()` - Timeline with risk alerts
- `create_top_risk_issuers()` - Top N high-risk issuers
- `create_comprehensive_dashboard()` - All plots at once

### 2. Data Loader (`data_loader.py`)

- `load_data_from_dynamodb()` - Load data from AWS DynamoDB
- `generate_sample_data()` - Generate realistic sample data
- `export_sample_data_to_csv()` - Export sample data to CSV

### 3. Panel Dashboard (`dashboard.py`)

Interactive web dashboard with:
- Multiple tabs: Overview, Risk Analysis, Asset Classes, Issuers, Delinquencies
- Real-time data refresh
- DynamoDB or sample data mode
- HTML export capability

### 4. QuickSight Setup (`quicksight_setup.py`)

Programmatically create AWS QuickSight dashboards:
- Create data sources from DynamoDB
- Create datasets
- Create analyses and dashboards
- Get embeddable dashboard URLs

## Quick Start

### Launch the Dashboard

Using the startup script (recommended):

```bash
# With sample data (no AWS credentials needed)
./scripts/start_dashboard.sh --sample-data

# With DynamoDB data
./scripts/start_dashboard.sh --region us-east-1

# Custom port
./scripts/start_dashboard.sh --sample-data --port 8080

# Save to HTML file
./scripts/start_dashboard.sh --sample-data --save-html dashboard.html
```

Using Python directly:

```bash
# With sample data
python -m src.visualization.dashboard --sample-data --port 5006

# With DynamoDB data
python -m src.visualization.dashboard --region us-east-1

# Save to HTML
python -m src.visualization.dashboard --sample-data --save-html output.html
```

### Use Plotting Functions

```python
from src.visualization import plot_utils
import pandas as pd

# Create sample data
data = pd.DataFrame({
    'filing_date': pd.date_range('2023-01-01', periods=100),
    'risk_score': np.random.beta(2, 5, 100)
})

# Create a plot
fig = plot_utils.create_risk_score_distribution(data)

# Display in Jupyter notebook
fig.show()

# Save to file
fig.write_html('risk_distribution.html')
```

### Generate Sample Data

```python
from src.visualization.data_loader import generate_sample_data, export_sample_data_to_csv

# Generate data
data = generate_sample_data(n_records=1000, n_issuers=20)

# Export to CSV
export_sample_data_to_csv('./sample_data')
```

### Setup QuickSight Dashboard

```bash
python -m src.visualization.quicksight_setup \
    --account-id 123456789012 \
    --principal-arn arn:aws:quicksight:us-east-1:123456789012:user/default/username \
    --region us-east-1 \
    --environment dev
```

## Dashboard Screenshots

The dashboard includes:

1. **Overview Tab**: Key metrics at a glance
   - Risk score distribution
   - Top high-risk issuers
   - Delinquency trends

2. **Risk Analysis Tab**: Deep dive into risk metrics
   - Risk score distribution with thresholds
   - Risk timeline with alerts

3. **Asset Classes Tab**: Performance by asset type
   - Average risk scores
   - Average delinquency rates

4. **Issuers Tab**: Issuer-specific analysis
   - Top risk issuers
   - Risk timeline by issuer

5. **Delinquencies Tab**: Delinquency tracking
   - Trends over time
   - Moving averages

## Data Format

### Expected DataFrame Formats

#### Risk Scores
```python
risk_scores_df = pd.DataFrame({
    'filing_date': pd.Series(dtype='datetime64[ns]'),
    'risk_score': pd.Series(dtype='float'),
    'filing_id': pd.Series(dtype='str'),
    'asset_class': pd.Series(dtype='str'),
    'issuer_name': pd.Series(dtype='str')
})
```

#### Delinquencies
```python
delinquencies_df = pd.DataFrame({
    'filing_date': pd.Series(dtype='datetime64[ns]'),
    'delinquency_rate': pd.Series(dtype='float')
})
```

#### Issuers
```python
issuers_df = pd.DataFrame({
    'issuer_name': pd.Series(dtype='str'),
    'filing_date': pd.Series(dtype='datetime64[ns]'),
    'risk_score': pd.Series(dtype='float'),
    'delinquency_rate': pd.Series(dtype='float'),
    'fico_score': pd.Series(dtype='float'),
    'pool_balance': pd.Series(dtype='float')
})
```

#### Asset Classes
```python
asset_classes_df = pd.DataFrame({
    'asset_class': pd.Series(dtype='str'),
    'avg_risk_score': pd.Series(dtype='float'),
    'avg_delinquency_rate': pd.Series(dtype='float')
})
```

## Dependencies

All required packages are in `requirements.txt`:

- `plotly>=5.18.0` - Interactive plotting
- `panel>=1.3.0` - Dashboard framework
- `bokeh>=3.3.0` - Panel backend
- `pandas>=2.1.0` - Data manipulation
- `numpy>=1.24.0` - Numerical operations
- `boto3>=1.34.0` - AWS SDK

## Configuration

The dashboard uses the same AWS configuration as the rest of the project:

- `config/aws_config.yaml` - AWS settings
- Environment variables from `.env` file
- AWS credentials from `~/.aws/credentials`

## Troubleshooting

### Dashboard won't start

1. Check dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Try with sample data first:
   ```bash
   ./scripts/start_dashboard.sh --sample-data
   ```

### DynamoDB connection errors

1. Verify AWS credentials:
   ```bash
   aws sts get-caller-identity
   ```

2. Check DynamoDB table names match environment
3. Ensure IAM permissions for DynamoDB read access

### QuickSight setup fails

1. Ensure QuickSight is enabled in your AWS account
2. Verify you have QuickSight admin permissions
3. Check the principal ARN format is correct
4. Ensure DynamoDB tables exist

## Performance

- **Dashboard loading**: ~2-3 seconds with sample data
- **DynamoDB queries**: Depends on table size and network
- **Refresh**: Manual refresh button available
- **Export HTML**: ~5-10 seconds for full dashboard

## Future Enhancements

- [ ] Auto-refresh capability
- [ ] Real-time streaming updates
- [ ] Additional visualization types
- [ ] Export to PDF
- [ ] Custom date range filters
- [ ] User authentication
- [ ] Multi-environment support
- [ ] Alerts and notifications integration

## Support

For issues or questions:
- Create an issue in the GitHub repository
- Check the main project documentation
- Review AWS QuickSight documentation for QuickSight-specific issues
