#!/bin/bash
# Run ABSolution Streamlit UI

echo "Starting ABSolution Streamlit UI..."
echo "Installing dependencies..."

pip install streamlit plotly altair matplotlib seaborn pandas numpy scikit-learn boto3 xgboost

echo ""
echo "Starting Streamlit server..."
streamlit run app.py
