"""
ABSolution Analytics Dashboard
Interactive dashboard for ABS portfolio analytics with SageMaker predictions
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objs as go
import pandas as pd
import os
from datetime import datetime
import logging

from sagemaker_client import SageMakerPredictor, generate_sample_historical_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Dash app
app = dash.Dash(
    __name__,
    title="ABSolution Analytics Dashboard",
    update_title="Loading..."
)

# Initialize SageMaker predictor
sagemaker_endpoint = os.environ.get('SAGEMAKER_ENDPOINT_NAME')
predictor = SageMakerPredictor(endpoint_name=sagemaker_endpoint)

# Generate or load historical data
logger.info("Loading historical delinquency data...")
historical_data = generate_sample_historical_data(n_periods=36)

# Generate initial predictions
logger.info("Generating initial predictions...")
initial_predictions = predictor.predict_delinquencies(historical_data, periods_ahead=12)


def create_delinquencies_figure(historical_data, predictions, show_confidence=True):
    """
    Create delinquencies chart figure

    Args:
        historical_data: DataFrame with historical data
        predictions: DataFrame with predictions
        show_confidence: Whether to show confidence intervals

    Returns:
        Plotly figure object
    """
    combined_data = pd.concat([historical_data, predictions], ignore_index=True)

    fig = go.Figure()

    if combined_data.empty:
        logger.error("No data available for chart")
        fig.add_annotation(
            text="No data available. Please check the logs.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="red")
        )
        return fig

    colors = {
        '30_days': {'historical': '#3498db', 'prediction': '#5dade2'},
        '60_days': {'historical': '#f39c12', 'prediction': '#f8c471'},
        '90_plus_days': {'historical': '#e74c3c', 'prediction': '#ec7063'}
    }

    categories = [
        ('delinquency_30_days', '30-Day Delinquencies', '30_days'),
        ('delinquency_60_days', '60-Day Delinquencies', '60_days'),
        ('delinquency_90_plus_days', '90+ Day Delinquencies', '90_plus_days')
    ]

    for col_name, display_name, color_key in categories:
        # Historical data (solid lines)
        historical_df = combined_data[~combined_data['is_prediction']]
        if not historical_df.empty:
            fig.add_trace(go.Scatter(
                x=historical_df['date'],
                y=historical_df[col_name],
                mode='lines+markers',
                name=f'{display_name} (Historical)',
                line=dict(color=colors[color_key]['historical'], width=3),
                marker=dict(size=6),
                hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Rate: %{y:.2%}<extra></extra>'
            ))

        # Predicted data (dashed lines)
        prediction_df = combined_data[combined_data['is_prediction']]
        if not prediction_df.empty:
            fig.add_trace(go.Scatter(
                x=prediction_df['date'],
                y=prediction_df[col_name],
                mode='lines+markers',
                name=f'{display_name} (Predicted)',
                line=dict(color=colors[color_key]['prediction'], width=3, dash='dash'),
                marker=dict(size=6, symbol='diamond'),
                hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Predicted Rate: %{y:.2%}<extra></extra>'
            ))

        # Add confidence intervals if enabled
        if show_confidence and not prediction_df.empty:
            # Upper confidence bound
            fig.add_trace(go.Scatter(
                x=prediction_df['date'],
                y=prediction_df[col_name] * 1.15,
                mode='lines',
                name=f'{display_name} Upper Bound',
                line=dict(color=colors[color_key]['prediction'], width=1, dash='dot'),
                opacity=0.3,
                showlegend=False,
                hoverinfo='skip'
            ))

            # Lower confidence bound
            fig.add_trace(go.Scatter(
                x=prediction_df['date'],
                y=prediction_df[col_name] * 0.85,
                mode='lines',
                name=f'{display_name} Lower Bound',
                line=dict(color=colors[color_key]['prediction'], width=1, dash='dot'),
                opacity=0.3,
                fill='tonexty',
                fillcolor=colors[color_key]['prediction'].replace(')', ', 0.1)').replace('rgb', 'rgba'),
                showlegend=False,
                hoverinfo='skip'
            ))

    # Add vertical line to separate historical from predictions
    if not historical_data.empty:
        last_historical_date = historical_data['date'].iloc[-1]
        # Add shape instead of vline to avoid timestamp issues
        fig.add_shape(
            type="line",
            x0=last_historical_date,
            x1=last_historical_date,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="gray", width=2, dash="dash"),
            opacity=0.5
        )
        # Add annotation
        fig.add_annotation(
            x=last_historical_date,
            y=1,
            yref="paper",
            text="Prediction Start",
            showarrow=False,
            yshift=10,
            font=dict(size=10, color="gray")
        )

    # Update layout
    fig.update_layout(
        title={
            'text': 'Delinquency Rates: Historical Data & ML Predictions',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        xaxis_title='Date',
        yaxis_title='Delinquency Rate (%)',
        yaxis_tickformat='.1%',
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font={'family': 'Arial, sans-serif'},
        height=600,
        xaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=0.5),
        yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=0.5)
    )

    return fig


# Create initial figure
initial_figure = create_delinquencies_figure(historical_data, initial_predictions, show_confidence=True)


# Dashboard Layout
app.layout = html.Div([
    html.Div([
        html.H1("ABSolution Analytics Dashboard", style={
            'textAlign': 'center',
            'color': '#2c3e50',
            'marginBottom': '10px',
            'fontFamily': 'Arial, sans-serif'
        }),
        html.P("AWS-Native ABS Analytics Platform with ML-Powered Predictions", style={
            'textAlign': 'center',
            'color': '#7f8c8d',
            'marginBottom': '30px',
            'fontFamily': 'Arial, sans-serif'
        }),
    ], style={'backgroundColor': '#ecf0f1', 'padding': '20px'}),

    # Delinquencies Panel
    html.Div([
        html.H2("Delinquencies Analysis", style={
            'color': '#34495e',
            'fontFamily': 'Arial, sans-serif',
            'marginBottom': '20px'
        }),
        html.Div([
            html.Div([
                html.Label("Prediction Periods:", style={'fontWeight': 'bold'}),
                dcc.Slider(
                    id='prediction-periods-slider',
                    min=3,
                    max=24,
                    step=3,
                    value=12,
                    marks={i: f"{i}m" for i in range(3, 25, 3)},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
            ], style={'width': '40%', 'display': 'inline-block', 'marginRight': '20px'}),

            html.Div([
                html.Label("Show Confidence Intervals:", style={'fontWeight': 'bold'}),
                dcc.Checklist(
                    id='show-confidence',
                    options=[{'label': ' Display', 'value': 'show'}],
                    value=['show'],
                    style={'marginTop': '10px'}
                ),
            ], style={'width': '20%', 'display': 'inline-block'}),
        ], style={'marginBottom': '20px'}),

        dcc.Graph(
            id='delinquencies-chart',
            figure=initial_figure,
            config={'displayModeBar': True, 'displaylogo': False}
        ),

        html.Div([
            html.H3("Model Information", style={'color': '#34495e', 'fontSize': '18px'}),
            html.P([
                html.Strong("SageMaker Endpoint: "),
                html.Span(sagemaker_endpoint or "Local Prediction Model (Fallback)",
                         style={'color': '#27ae60' if sagemaker_endpoint else '#e74c3c'})
            ]),
            html.P([
                html.Strong("Last Updated: "),
                html.Span(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            ]),
        ], style={
            'backgroundColor': '#f8f9fa',
            'padding': '15px',
            'borderRadius': '5px',
            'marginTop': '20px'
        })
    ], style={
        'backgroundColor': 'white',
        'padding': '30px',
        'margin': '20px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),

    # Additional Metrics Panel
    html.Div([
        html.H2("Portfolio Metrics", style={
            'color': '#34495e',
            'fontFamily': 'Arial, sans-serif',
            'marginBottom': '20px'
        }),
        html.Div([
            html.Div([
                html.H4("Current 30-Day Delinquency", style={'color': '#3498db'}),
                html.H3(f"{historical_data['delinquency_30_days'].iloc[-1]:.2%}",
                       style={'color': '#2c3e50', 'fontSize': '32px'})
            ], style={
                'backgroundColor': '#ecf0f1',
                'padding': '20px',
                'borderRadius': '5px',
                'textAlign': 'center',
                'width': '30%',
                'display': 'inline-block',
                'marginRight': '2%'
            }),

            html.Div([
                html.H4("Current 60-Day Delinquency", style={'color': '#f39c12'}),
                html.H3(f"{historical_data['delinquency_60_days'].iloc[-1]:.2%}",
                       style={'color': '#2c3e50', 'fontSize': '32px'})
            ], style={
                'backgroundColor': '#ecf0f1',
                'padding': '20px',
                'borderRadius': '5px',
                'textAlign': 'center',
                'width': '30%',
                'display': 'inline-block',
                'marginRight': '2%'
            }),

            html.Div([
                html.H4("Current 90+ Day Delinquency", style={'color': '#e74c3c'}),
                html.H3(f"{historical_data['delinquency_90_plus_days'].iloc[-1]:.2%}",
                       style={'color': '#2c3e50', 'fontSize': '32px'})
            ], style={
                'backgroundColor': '#ecf0f1',
                'padding': '20px',
                'borderRadius': '5px',
                'textAlign': 'center',
                'width': '30%',
                'display': 'inline-block'
            }),
        ])
    ], style={
        'backgroundColor': 'white',
        'padding': '30px',
        'margin': '20px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),

    # Footer
    html.Div([
        html.P("© 2024 ABSolution | Powered by AWS SageMaker, Kinesis, Athena, QuickSight",
               style={'textAlign': 'center', 'color': '#95a5a6'})
    ], style={'padding': '20px'})
], style={'backgroundColor': '#f5f6fa', 'minHeight': '100vh'})


@callback(
    Output('delinquencies-chart', 'figure'),
    [Input('prediction-periods-slider', 'value'),
     Input('show-confidence', 'value')]
)
def update_delinquencies_chart(prediction_periods, show_confidence):
    """
    Update delinquencies chart with historical data and predictions

    Args:
        prediction_periods: Number of future periods to predict
        show_confidence: Whether to show confidence intervals

    Returns:
        Plotly figure object
    """
    if prediction_periods is None:
        prediction_periods = 12

    logger.info(f"Updating chart with {prediction_periods} prediction periods")
    logger.info(f"Show confidence: {show_confidence}")

    # Generate fresh predictions based on slider value
    fresh_predictions = predictor.predict_delinquencies(
        historical_data,
        periods_ahead=prediction_periods
    )

    logger.info(f"Generated {len(fresh_predictions)} prediction records")

    # Determine if confidence intervals should be shown
    show_conf = show_confidence and 'show' in show_confidence

    # Create figure using helper function
    fig = create_delinquencies_figure(historical_data, fresh_predictions, show_confidence=show_conf)

    return fig


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'

    logger.info(f"Starting ABSolution Dashboard on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"SageMaker endpoint: {sagemaker_endpoint or 'Not configured (using local predictions)'}")

    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=port
    )
