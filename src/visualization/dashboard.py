"""
Panel-based Interactive Dashboard for ABS Analytics
Displays all plots in a comprehensive web interface
"""

import panel as pn
import pandas as pd
import boto3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from .plot_utils import (
    create_risk_score_distribution,
    create_delinquency_trends,
    create_asset_class_comparison,
    create_issuer_performance,
    create_risk_timeline,
    create_top_risk_issuers,
    create_comprehensive_dashboard
)
from .data_loader import load_data_from_dynamodb, generate_sample_data

# Initialize Panel extension
pn.extension('plotly')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ABSolutionDashboard:
    """
    Main dashboard class for ABS Analytics visualization
    """

    def __init__(self, use_sample_data: bool = False, aws_region: str = 'us-east-1'):
        """
        Initialize the dashboard

        Args:
            use_sample_data: If True, use generated sample data instead of DynamoDB
            aws_region: AWS region for DynamoDB access
        """
        self.use_sample_data = use_sample_data
        self.aws_region = aws_region
        self.data = {}
        self.plots = {}

        # Dashboard title
        self.title = pn.pane.Markdown(
            "# ABSolution Analytics Dashboard\n## Real-time ABS Performance Monitoring",
            styles={'background': '#1f77b4', 'color': 'white', 'padding': '20px',
                   'border-radius': '5px'}
        )

        # Status indicator
        self.status = pn.pane.Markdown("**Status:** Initializing...", styles={'padding': '10px'})

        # Create refresh button
        self.refresh_button = pn.widgets.Button(name='Refresh Data', button_type='primary')
        self.refresh_button.on_click(self.refresh_data)

        # Initialize data
        self.load_data()

    def load_data(self):
        """Load data from DynamoDB or generate sample data"""
        try:
            self.status.object = "**Status:** Loading data..."

            if self.use_sample_data:
                logger.info("Generating sample data...")
                self.data = generate_sample_data()
                self.status.object = "**Status:** ✓ Sample data loaded"
            else:
                logger.info("Loading data from DynamoDB...")
                self.data = load_data_from_dynamodb(region=self.aws_region)
                self.status.object = f"**Status:** ✓ Data loaded from DynamoDB ({len(self.data)} datasets)"

            # Create plots
            self.create_plots()

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.status.object = f"**Status:** ✗ Error loading data: {str(e)}"
            # Fallback to sample data
            self.data = generate_sample_data()
            self.create_plots()

    def create_plots(self):
        """Create all visualization plots"""
        try:
            logger.info("Creating plots...")

            # Create individual plots
            if 'risk_scores' in self.data and not self.data['risk_scores'].empty:
                self.plots['risk_distribution'] = pn.pane.Plotly(
                    create_risk_score_distribution(self.data['risk_scores']),
                    sizing_mode='stretch_width'
                )

            if 'delinquencies' in self.data and not self.data['delinquencies'].empty:
                self.plots['delinquency_trends'] = pn.pane.Plotly(
                    create_delinquency_trends(self.data['delinquencies']),
                    sizing_mode='stretch_width'
                )

            if 'asset_classes' in self.data and not self.data['asset_classes'].empty:
                self.plots['asset_comparison'] = pn.pane.Plotly(
                    create_asset_class_comparison(self.data['asset_classes']),
                    sizing_mode='stretch_width'
                )

            if 'issuers' in self.data and not self.data['issuers'].empty:
                self.plots['risk_timeline'] = pn.pane.Plotly(
                    create_risk_timeline(self.data['issuers']),
                    sizing_mode='stretch_width'
                )
                self.plots['top_risk_issuers'] = pn.pane.Plotly(
                    create_top_risk_issuers(self.data['issuers']),
                    sizing_mode='stretch_width'
                )

            logger.info(f"Created {len(self.plots)} plots")

        except Exception as e:
            logger.error(f"Error creating plots: {e}")
            self.status.object = f"**Status:** ✗ Error creating plots: {str(e)}"

    def refresh_data(self, event=None):
        """Refresh data and recreate plots"""
        logger.info("Refreshing data...")
        self.load_data()
        self.status.object = "**Status:** ✓ Data refreshed"

    def create_layout(self) -> pn.Column:
        """
        Create the dashboard layout with all plots

        Returns:
            Panel Column layout
        """
        # Header section
        header = pn.Column(
            self.title,
            pn.Row(self.status, pn.Spacer(), self.refresh_button),
            styles={'background': '#f5f5f5', 'padding': '10px', 'border-radius': '5px'}
        )

        # Create tabs for different sections
        tabs = pn.Tabs()

        # Overview Tab - Key metrics
        overview_tab = pn.Column(
            pn.pane.Markdown("## Overview Dashboard", styles={'padding': '10px'}),
            pn.Row(
                self.plots.get('risk_distribution', pn.pane.Markdown("No data available")),
                self.plots.get('top_risk_issuers', pn.pane.Markdown("No data available")),
                sizing_mode='stretch_width'
            ),
            pn.Row(
                self.plots.get('delinquency_trends', pn.pane.Markdown("No data available")),
                sizing_mode='stretch_width'
            )
        )
        tabs.append(('Overview', overview_tab))

        # Risk Analysis Tab
        risk_tab = pn.Column(
            pn.pane.Markdown("## Risk Analysis", styles={'padding': '10px'}),
            self.plots.get('risk_distribution', pn.pane.Markdown("No data available")),
            self.plots.get('risk_timeline', pn.pane.Markdown("No data available")),
            sizing_mode='stretch_width'
        )
        tabs.append(('Risk Analysis', risk_tab))

        # Asset Classes Tab
        asset_tab = pn.Column(
            pn.pane.Markdown("## Asset Class Performance", styles={'padding': '10px'}),
            self.plots.get('asset_comparison', pn.pane.Markdown("No data available")),
            sizing_mode='stretch_width'
        )
        tabs.append(('Asset Classes', asset_tab))

        # Issuers Tab
        issuers_tab = pn.Column(
            pn.pane.Markdown("## Issuer Analysis", styles={'padding': '10px'}),
            self.plots.get('top_risk_issuers', pn.pane.Markdown("No data available")),
            self.plots.get('risk_timeline', pn.pane.Markdown("No data available")),
            sizing_mode='stretch_width'
        )
        tabs.append(('Issuers', issuers_tab))

        # Delinquency Tab
        delinquency_tab = pn.Column(
            pn.pane.Markdown("## Delinquency Trends", styles={'padding': '10px'}),
            self.plots.get('delinquency_trends', pn.pane.Markdown("No data available")),
            sizing_mode='stretch_width'
        )
        tabs.append(('Delinquencies', delinquency_tab))

        # Complete layout
        layout = pn.Column(
            header,
            tabs,
            sizing_mode='stretch_width',
            styles={'padding': '20px'}
        )

        return layout

    def serve(self, port: int = 5006, show: bool = True):
        """
        Serve the dashboard on a local web server

        Args:
            port: Port number to serve on
            show: Whether to open browser automatically
        """
        logger.info(f"Starting dashboard server on port {port}...")
        layout = self.create_layout()
        pn.serve(layout, port=port, show=show, title="ABSolution Analytics Dashboard")

    def save_to_html(self, filename: str = 'dashboard.html'):
        """
        Save dashboard to static HTML file

        Args:
            filename: Output filename
        """
        logger.info(f"Saving dashboard to {filename}...")
        layout = self.create_layout()
        layout.save(filename)
        logger.info(f"Dashboard saved to {filename}")


def main():
    """Main entry point for the dashboard"""
    import argparse

    parser = argparse.ArgumentParser(description='ABSolution Analytics Dashboard')
    parser.add_argument('--sample-data', action='store_true',
                       help='Use sample data instead of DynamoDB')
    parser.add_argument('--port', type=int, default=5006,
                       help='Port to serve dashboard on (default: 5006)')
    parser.add_argument('--region', type=str, default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--save-html', type=str,
                       help='Save dashboard to HTML file instead of serving')
    parser.add_argument('--no-browser', action='store_true',
                       help='Do not open browser automatically')

    args = parser.parse_args()

    # Create dashboard
    dashboard = ABSolutionDashboard(
        use_sample_data=args.sample_data,
        aws_region=args.region
    )

    if args.save_html:
        dashboard.save_to_html(args.save_html)
    else:
        dashboard.serve(port=args.port, show=not args.no_browser)


if __name__ == '__main__':
    main()
