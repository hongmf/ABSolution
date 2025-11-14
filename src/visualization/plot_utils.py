"""
Plotting utilities for ABS analytics visualization
Provides functions to create various plots and charts for the dashboard
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


def create_risk_score_distribution(data: pd.DataFrame, title: str = "Risk Score Distribution") -> go.Figure:
    """
    Create a histogram showing distribution of risk scores

    Args:
        data: DataFrame with 'risk_score' column
        title: Plot title

    Returns:
        Plotly figure object
    """
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=data['risk_score'],
        nbinsx=50,
        name='Risk Scores',
        marker=dict(
            color='rgba(54, 162, 235, 0.7)',
            line=dict(color='rgba(54, 162, 235, 1)', width=1)
        ),
        hovertemplate='Risk Score: %{x:.3f}<br>Count: %{y}<extra></extra>'
    ))

    # Add threshold lines
    fig.add_vline(x=0.75, line_dash="dash", line_color="red",
                  annotation_text="High Risk Threshold (0.75)")
    fig.add_vline(x=0.5, line_dash="dash", line_color="orange",
                  annotation_text="Medium Risk Threshold (0.5)")

    fig.update_layout(
        title=title,
        xaxis_title="Risk Score",
        yaxis_title="Count",
        template="plotly_white",
        hovermode='x',
        showlegend=True,
        height=400
    )

    return fig


def create_delinquency_trends(data: pd.DataFrame, title: str = "Delinquency Trends Over Time") -> go.Figure:
    """
    Create a time series plot of delinquency rates

    Args:
        data: DataFrame with 'filing_date' and 'delinquency_rate' columns
        title: Plot title

    Returns:
        Plotly figure object
    """
    # Ensure data is sorted by date
    data = data.sort_values('filing_date')

    fig = go.Figure()

    # Add delinquency rate line
    fig.add_trace(go.Scatter(
        x=data['filing_date'],
        y=data['delinquency_rate'],
        mode='lines+markers',
        name='Delinquency Rate',
        line=dict(color='rgb(255, 99, 132)', width=2),
        marker=dict(size=6),
        hovertemplate='Date: %{x}<br>Rate: %{y:.2%}<extra></extra>'
    ))

    # Add moving average if enough data
    if len(data) > 7:
        data['ma_7'] = data['delinquency_rate'].rolling(window=7).mean()
        fig.add_trace(go.Scatter(
            x=data['filing_date'],
            y=data['ma_7'],
            mode='lines',
            name='7-Day Moving Average',
            line=dict(color='rgb(75, 192, 192)', width=2, dash='dot'),
            hovertemplate='Date: %{x}<br>MA: %{y:.2%}<extra></extra>'
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Delinquency Rate",
        yaxis_tickformat='.1%',
        template="plotly_white",
        hovermode='x unified',
        showlegend=True,
        height=400
    )

    return fig


def create_asset_class_comparison(data: pd.DataFrame, title: str = "Asset Class Performance Comparison") -> go.Figure:
    """
    Create a grouped bar chart comparing asset classes

    Args:
        data: DataFrame with 'asset_class', 'avg_risk_score', 'avg_delinquency_rate' columns
        title: Plot title

    Returns:
        Plotly figure object
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Average Risk Score by Asset Class', 'Average Delinquency Rate by Asset Class'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )

    # Sort by risk score
    data = data.sort_values('avg_risk_score', ascending=False)

    # Risk score bars
    fig.add_trace(
        go.Bar(
            x=data['asset_class'],
            y=data['avg_risk_score'],
            name='Avg Risk Score',
            marker=dict(color='rgb(255, 159, 64)'),
            hovertemplate='%{x}<br>Risk Score: %{y:.3f}<extra></extra>'
        ),
        row=1, col=1
    )

    # Delinquency rate bars
    fig.add_trace(
        go.Bar(
            x=data['asset_class'],
            y=data['avg_delinquency_rate'],
            name='Avg Delinquency Rate',
            marker=dict(color='rgb(153, 102, 255)'),
            hovertemplate='%{x}<br>Delinquency: %{y:.2%}<extra></extra>'
        ),
        row=1, col=2
    )

    fig.update_yaxes(title_text="Risk Score", row=1, col=1)
    fig.update_yaxes(title_text="Delinquency Rate", tickformat='.1%', row=1, col=2)
    fig.update_xaxes(title_text="Asset Class", row=1, col=1)
    fig.update_xaxes(title_text="Asset Class", row=1, col=2)

    fig.update_layout(
        title_text=title,
        template="plotly_white",
        showlegend=False,
        height=400
    )

    return fig


def create_issuer_performance(data: pd.DataFrame, issuer_name: str = None,
                             title: str = "Issuer Performance Over Time") -> go.Figure:
    """
    Create a multi-metric dashboard for issuer performance

    Args:
        data: DataFrame with issuer metrics over time
        issuer_name: Name of the issuer (optional, for title)
        title: Plot title

    Returns:
        Plotly figure object
    """
    if issuer_name:
        title = f"{title} - {issuer_name}"

    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Risk Score Trend',
            'FICO Score Distribution',
            'Delinquency Rate',
            'Pool Balance'
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'histogram'}],
            [{'type': 'scatter'}, {'type': 'scatter'}]
        ]
    )

    # Risk score trend
    if 'filing_date' in data.columns and 'risk_score' in data.columns:
        fig.add_trace(
            go.Scatter(
                x=data['filing_date'],
                y=data['risk_score'],
                mode='lines+markers',
                name='Risk Score',
                line=dict(color='red'),
                hovertemplate='%{x}<br>Risk: %{y:.3f}<extra></extra>'
            ),
            row=1, col=1
        )

    # FICO score distribution
    if 'fico_score' in data.columns:
        fig.add_trace(
            go.Histogram(
                x=data['fico_score'],
                name='FICO Distribution',
                marker=dict(color='blue'),
                hovertemplate='FICO: %{x}<br>Count: %{y}<extra></extra>'
            ),
            row=1, col=2
        )

    # Delinquency rate trend
    if 'filing_date' in data.columns and 'delinquency_rate' in data.columns:
        fig.add_trace(
            go.Scatter(
                x=data['filing_date'],
                y=data['delinquency_rate'],
                mode='lines+markers',
                name='Delinquency Rate',
                line=dict(color='orange'),
                hovertemplate='%{x}<br>Rate: %{y:.2%}<extra></extra>'
            ),
            row=2, col=1
        )

    # Pool balance trend
    if 'filing_date' in data.columns and 'pool_balance' in data.columns:
        fig.add_trace(
            go.Scatter(
                x=data['filing_date'],
                y=data['pool_balance'],
                mode='lines+markers',
                name='Pool Balance',
                line=dict(color='green'),
                hovertemplate='%{x}<br>Balance: $%{y:,.0f}<extra></extra>'
            ),
            row=2, col=2
        )

    fig.update_layout(
        title_text=title,
        template="plotly_white",
        showlegend=False,
        height=600
    )

    return fig


def create_risk_timeline(data: pd.DataFrame, title: str = "Risk Score Timeline") -> go.Figure:
    """
    Create an interactive timeline of risk scores with annotations for high-risk events

    Args:
        data: DataFrame with 'filing_date', 'risk_score', 'issuer_name' columns
        title: Plot title

    Returns:
        Plotly figure object
    """
    fig = go.Figure()

    # Sort by date
    data = data.sort_values('filing_date')

    # Add scatter plot for each issuer if multiple issuers
    if 'issuer_name' in data.columns:
        for issuer in data['issuer_name'].unique():
            issuer_data = data[data['issuer_name'] == issuer]
            fig.add_trace(go.Scatter(
                x=issuer_data['filing_date'],
                y=issuer_data['risk_score'],
                mode='lines+markers',
                name=issuer,
                marker=dict(size=8),
                hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Risk: %{y:.3f}<extra></extra>'
            ))
    else:
        fig.add_trace(go.Scatter(
            x=data['filing_date'],
            y=data['risk_score'],
            mode='lines+markers',
            name='Risk Score',
            marker=dict(size=8, color='blue'),
            hovertemplate='Date: %{x}<br>Risk: %{y:.3f}<extra></extra>'
        ))

    # Add high-risk threshold line
    fig.add_hline(y=0.75, line_dash="dash", line_color="red",
                  annotation_text="High Risk Threshold")

    # Highlight high-risk points
    high_risk = data[data['risk_score'] > 0.75]
    if not high_risk.empty:
        fig.add_trace(go.Scatter(
            x=high_risk['filing_date'],
            y=high_risk['risk_score'],
            mode='markers',
            name='High Risk Alert',
            marker=dict(
                size=12,
                color='red',
                symbol='diamond',
                line=dict(color='darkred', width=2)
            ),
            hovertemplate='<b>HIGH RISK</b><br>Date: %{x}<br>Risk: %{y:.3f}<extra></extra>'
        ))

    fig.update_layout(
        title=title,
        xaxis_title="Filing Date",
        yaxis_title="Risk Score",
        template="plotly_white",
        hovermode='closest',
        showlegend=True,
        height=500
    )

    return fig


def create_top_risk_issuers(data: pd.DataFrame, top_n: int = 10,
                           title: str = "Top High-Risk Issuers") -> go.Figure:
    """
    Create a bar chart of top N high-risk issuers

    Args:
        data: DataFrame with 'issuer_name', 'risk_score', 'filing_date' columns
        top_n: Number of top issuers to show
        title: Plot title

    Returns:
        Plotly figure object
    """
    # Get the latest risk score for each issuer
    latest_scores = data.sort_values('filing_date').groupby('issuer_name').last().reset_index()

    # Get top N by risk score
    top_issuers = latest_scores.nlargest(top_n, 'risk_score')

    # Create color scale based on risk level
    colors = ['red' if score > 0.75 else 'orange' if score > 0.5 else 'yellow'
              for score in top_issuers['risk_score']]

    fig = go.Figure(data=[
        go.Bar(
            x=top_issuers['risk_score'],
            y=top_issuers['issuer_name'],
            orientation='h',
            marker=dict(color=colors),
            hovertemplate='<b>%{y}</b><br>Risk Score: %{x:.3f}<extra></extra>'
        )
    ])

    # Add threshold lines
    fig.add_vline(x=0.75, line_dash="dash", line_color="darkred",
                  annotation_text="High Risk (0.75)")
    fig.add_vline(x=0.5, line_dash="dash", line_color="darkorange",
                  annotation_text="Medium Risk (0.5)")

    fig.update_layout(
        title=title,
        xaxis_title="Risk Score",
        yaxis_title="Issuer",
        template="plotly_white",
        showlegend=False,
        height=max(400, top_n * 40)  # Dynamic height based on number of issuers
    )

    return fig


def create_comprehensive_dashboard(data: Dict[str, pd.DataFrame]) -> Dict[str, go.Figure]:
    """
    Create all dashboard plots at once

    Args:
        data: Dictionary with keys:
            - 'risk_scores': DataFrame with risk score data
            - 'delinquencies': DataFrame with delinquency data
            - 'asset_classes': DataFrame with asset class metrics
            - 'issuers': DataFrame with issuer data

    Returns:
        Dictionary of plot names to Plotly figures
    """
    plots = {}

    if 'risk_scores' in data and not data['risk_scores'].empty:
        plots['risk_distribution'] = create_risk_score_distribution(data['risk_scores'])

    if 'delinquencies' in data and not data['delinquencies'].empty:
        plots['delinquency_trends'] = create_delinquency_trends(data['delinquencies'])

    if 'asset_classes' in data and not data['asset_classes'].empty:
        plots['asset_comparison'] = create_asset_class_comparison(data['asset_classes'])

    if 'issuers' in data and not data['issuers'].empty:
        plots['risk_timeline'] = create_risk_timeline(data['issuers'])
        plots['top_risk_issuers'] = create_top_risk_issuers(data['issuers'])

    return plots
