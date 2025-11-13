import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import sys
import os

# Set matplotlib backend
import matplotlib
matplotlib.use('Agg')

# Add paths for imports
sys.path.append('.')
sys.path.append('./scripts')
sys.path.append('./prompt')

from prompt.visualization_prompt import get_visualization_prompt
from scripts.bedrock_claude import call_bedrock_claude
from scripts.safe_convert import safe_numeric_conversion
from dotenv import load_dotenv

load_dotenv()

st.title("ABSolution Visualization Agent")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('scripts/Delinquency_prediction_dataset.csv')
    df = safe_numeric_conversion(df)
    return df

df = load_data()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Configuration in sidebar
with st.sidebar:
    st.subheader("Configuration")
    st.write(f"AWS Region: {os.getenv('BEDROCK_REGION', 'us-west-2')}")
    st.write(f"S3 Bucket: {os.getenv('S3_BUCKET_NAME', 'abs-ee')}")
    
    st.subheader("Dataset Overview")
    st.write(f"Shape: {df.shape}")
    st.write("Numeric:", df.select_dtypes(include=[np.number]).columns.tolist())
    st.write("Categorical:", df.select_dtypes(exclude=[np.number]).columns.tolist())

# Chat input
if prompt := st.chat_input("Ask for a visualization..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        try:
            with st.spinner("Generating visualization..."):
                # Get data summary
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
                
                data_summary = f"""
                Dataset: Delinquency Prediction Dataset
                Shape: {df.shape}
                Numeric columns: {numeric_cols}
                Categorical columns: {categorical_cols}
                Sample data:
                {df.head().to_string()}
                """
                
                # Get visualization prompt
                viz_prompt = get_visualization_prompt(prompt)
                
                try:
                    # Call Claude via Bedrock
                    recommendations = call_bedrock_claude(viz_prompt, data_summary)
                    st.markdown(recommendations)
                    
                    # Always generate a plot
                    st.subheader("📊 Generated Visualization")
                    
                    if "credit score" in prompt.lower():
                        fig, ax = plt.subplots(figsize=(10, 6))
                        df['Credit_Score'].hist(bins=30, ax=ax, color='skyblue', alpha=0.7)
                        ax.set_title('Credit Score Distribution', fontsize=16)
                        ax.set_xlabel('Credit Score')
                        ax.set_ylabel('Frequency')
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                        
                    elif "employment" in prompt.lower():
                        fig, ax = plt.subplots(figsize=(10, 6))
                        df['Employment_Status'].value_counts().plot(kind='bar', ax=ax, color='lightcoral')
                        ax.set_title('Employment Status Distribution', fontsize=16)
                        ax.set_xlabel('Employment Status')
                        ax.set_ylabel('Count')
                        plt.xticks(rotation=45)
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                        
                    elif "income" in prompt.lower():
                        fig, ax = plt.subplots(figsize=(10, 6))
                        df['Income'].hist(bins=30, ax=ax, color='lightgreen', alpha=0.7)
                        ax.set_title('Income Distribution', fontsize=16)
                        ax.set_xlabel('Income')
                        ax.set_ylabel('Frequency')
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                        
                    elif "age" in prompt.lower():
                        fig, ax = plt.subplots(figsize=(10, 6))
                        df['Age'].hist(bins=20, ax=ax, color='orange', alpha=0.7)
                        ax.set_title('Age Distribution', fontsize=16)
                        ax.set_xlabel('Age')
                        ax.set_ylabel('Frequency')
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                        
                    else:
                        # Default plot - correlation matrix
                        fig, ax = plt.subplots(figsize=(12, 8))
                        numeric_cols = df.select_dtypes(include=[np.number]).columns
                        correlation_matrix = df[numeric_cols].corr()
                        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', ax=ax, fmt='.2f')
                        ax.set_title('Correlation Matrix', fontsize=16)
                        st.pyplot(fig)
                    
                    # Add assistant message to chat history
                    st.session_state.messages.append({"role": "assistant", "content": recommendations})
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
        except Exception as e:
            error_msg = f"Error calling Claude: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})