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
from scripts.s3_data_loader import list_s3_folders, list_s3_files, load_s3_file
from scripts.dynamodb_loader import load_dynamodb_table, list_dynamodb_tables
from dotenv import load_dotenv

load_dotenv()

st.title("ABSolution Visualization Agent")

# Initialize session state
if "current_df" not in st.session_state:
    st.session_state.current_df = None
    st.session_state.current_source = "No data selected"
    st.session_state.file_selected = False

# Use selected data or default
if st.session_state.current_df is not None:
    df = st.session_state.current_df
else:
    # Load default data
    df = pd.read_csv('scripts/Delinquency_prediction_dataset.csv')
    df = safe_numeric_conversion(df)
    st.session_state.current_df = df
    st.session_state.current_source = "Default: Delinquency_prediction_dataset.csv"
    st.session_state.file_selected = True

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Configuration in sidebar
with st.sidebar:
    st.subheader("Data Source")
    st.write(f"Current: {st.session_state.current_source}")
    
    # DynamoDB Data Source
    st.subheader("💾 DynamoDB Tables")
    try:
        tables = list_dynamodb_tables()
        if tables:
            selected_table = st.selectbox("Select Table:", ["Select..."] + tables)
            
            if selected_table != "Select..." and st.button("Load DynamoDB Data"):
                with st.spinner("Loading data from DynamoDB..."):
                    try:
                        new_df = load_dynamodb_table(selected_table)
                        st.session_state.current_df = safe_numeric_conversion(new_df)
                        st.session_state.current_source = f"DynamoDB: {selected_table}"
                        st.session_state.file_selected = True
                        st.success(f"Loaded {new_df.shape[0]} rows, {new_df.shape[1]} columns")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading table: {str(e)}")
        else:
            st.write("No DynamoDB tables found")
    except Exception as e:
        st.error(f"DynamoDB Error: {str(e)}")
    
    # S3 Data Browser
    st.subheader("📁 S3 Data Browser")
    try:
        folders = list_s3_folders()
        if folders:
            selected_folder = st.selectbox("Select Folder:", ["Select..."] + folders)
            
            if selected_folder != "Select...":
                files = list_s3_files(selected_folder)
                if files:
                    selected_file = st.selectbox("Select File:", ["Select..."] + files)
                    
                    if selected_file != "Select..." and st.button("Load Data"):
                        with st.spinner("Loading data from S3..."):
                            try:
                                new_df = load_s3_file(selected_file)
                                st.session_state.current_df = safe_numeric_conversion(new_df)
                                st.session_state.current_source = f"S3: {selected_file}"
                                st.session_state.file_selected = True
                                st.success(f"Loaded {new_df.shape[0]} rows, {new_df.shape[1]} columns")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error loading file: {str(e)}")
                else:
                    st.write("No files found in folder")
        else:
            st.write("No folders found in S3")
    except Exception as e:
        st.error(f"S3 Error: {str(e)}")
    
    st.subheader("Configuration")
    st.write(f"AWS Region: {os.getenv('BEDROCK_REGION', 'us-west-2')}")
    st.write(f"S3 Bucket: {os.getenv('S3_BUCKET_NAME', 'abs-ee')}")
    
    st.subheader("Dataset Overview")
    st.write(f"Shape: {df.shape}")
    st.write("Numeric:", df.select_dtypes(include=[np.number]).columns.tolist())
    st.write("Categorical:", df.select_dtypes(exclude=[np.number]).columns.tolist())
    
    # Use default data button
    if not st.session_state.file_selected:
        if st.button("📊 Use Default Dataset"):
            default_df = pd.read_csv('scripts/Delinquency_prediction_dataset.csv')
            st.session_state.current_df = safe_numeric_conversion(default_df)
            st.session_state.current_source = "Default: Delinquency_prediction_dataset.csv"
            st.session_state.file_selected = True
            st.rerun()
    else:
        if st.button("🔄 Clear Selection"):
            st.session_state.current_df = None
            st.session_state.current_source = "No data selected"
            st.session_state.file_selected = False
            st.rerun()

# File browser for plotting
st.subheader("📁 Quick File Browser")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Browse & Plot Data"):
        st.session_state.show_browser = True
        
with col2:
    if st.button("💾 Load AutoLoanMetrics"):
        with st.spinner("Loading AutoLoanMetrics from DynamoDB..."):
            try:
                new_df = load_dynamodb_table('AutoLoanMetrics')
                st.session_state.current_df = safe_numeric_conversion(new_df)
                st.session_state.current_source = "DynamoDB: AutoLoanMetrics"
                st.session_state.file_selected = True
                st.success(f"Loaded {new_df.shape[0]} rows, {new_df.shape[1]} columns")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

if "show_browser" in st.session_state and st.session_state.show_browser:
    with st.expander("Select Data File", expanded=True):
        try:
            folders = list_s3_folders()
            if folders:
                folder = st.selectbox("Folder:", folders, key="plot_folder")
                files = list_s3_files(folder)
                if files:
                    file = st.selectbox("File:", files, key="plot_file")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Load & Plot", key="load_plot"):
                            with st.spinner("Loading and plotting..."):
                                try:
                                    new_df = load_s3_file(file)
                                    st.session_state.current_df = safe_numeric_conversion(new_df)
                                    st.session_state.current_source = f"S3: {file}"
                                    st.session_state.file_selected = True
                                    st.session_state.show_browser = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                    with col_b:
                        if st.button("Cancel", key="cancel_plot"):
                            st.session_state.show_browser = False
                            st.rerun()
        except Exception as e:
            st.error(f"S3 Error: {str(e)}")

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
                Dataset: {st.session_state.current_source}
                Shape: {df.shape}
                Numeric columns: {numeric_cols}
                Categorical columns: {categorical_cols}
                Sample data:
                {df.head().to_string()}
                """
                
                # Get visualization prompt
                viz_prompt = get_visualization_prompt(prompt)
                
                try:
                    # Show data overview first
                    st.subheader("📊 Data Overview")
                    st.write(f"**Dataset Size:** {df.shape[0]} rows × {df.shape[1]} columns")
                    st.write("**First 5 rows:**")
                    st.dataframe(df.head())
                    
                    # Call Claude via Bedrock
                    recommendations = call_bedrock_claude(viz_prompt, data_summary)
                    st.markdown(recommendations)
                    
                    # Generate multiple plots
                    st.subheader("📊 Generated Visualizations")
                    
                    # Create 2x2 grid of plots
                    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
                    
                    # Plot 1: Credit Score Distribution
                    if 'Credit_Score' in df.columns:
                        df['Credit_Score'].hist(bins=20, ax=ax1, color='skyblue', alpha=0.7)
                        ax1.set_title('Credit Score Distribution')
                        ax1.set_xlabel('Credit Score')
                        ax1.set_ylabel('Frequency')
                        ax1.grid(True, alpha=0.3)
                    
                    # Plot 2: Employment Status
                    if 'Employment_Status' in df.columns:
                        df['Employment_Status'].value_counts().plot(kind='bar', ax=ax2, color='lightcoral')
                        ax2.set_title('Employment Status Distribution')
                        ax2.set_xlabel('Employment Status')
                        ax2.set_ylabel('Count')
                        ax2.tick_params(axis='x', rotation=45)
                        ax2.grid(True, alpha=0.3)
                    
                    # Plot 3: Income Distribution
                    if 'Income' in df.columns:
                        df['Income'].hist(bins=20, ax=ax3, color='lightgreen', alpha=0.7)
                        ax3.set_title('Income Distribution')
                        ax3.set_xlabel('Income')
                        ax3.set_ylabel('Frequency')
                        ax3.grid(True, alpha=0.3)
                    
                    # Plot 4: Scatter Plot (Income vs Credit Score)
                    if 'Income' in df.columns and 'Credit_Score' in df.columns:
                        ax4.scatter(df['Income'], df['Credit_Score'], alpha=0.6, color='purple')
                        ax4.set_title('Income vs Credit Score')
                        ax4.set_xlabel('Income')
                        ax4.set_ylabel('Credit Score')
                        ax4.grid(True, alpha=0.3)
                    elif 'Age' in df.columns:
                        df['Age'].hist(bins=15, ax=ax4, color='orange', alpha=0.7)
                        ax4.set_title('Age Distribution')
                        ax4.set_xlabel('Age')
                        ax4.set_ylabel('Frequency')
                        ax4.grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Additional scatter plots
                    if len(numeric_cols) >= 2:
                        st.subheader("📈 Relationship Analysis")
                        fig3, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(16, 6))
                        
                        # Scatter plot 1: Age vs Income
                        if 'Age' in df.columns and 'Income' in df.columns:
                            ax_left.scatter(df['Age'], df['Income'], alpha=0.6, color='green')
                            ax_left.set_title('Age vs Income')
                            ax_left.set_xlabel('Age')
                            ax_left.set_ylabel('Income')
                            ax_left.grid(True, alpha=0.3)
                        
                        # Scatter plot 2: Credit Utilization vs Loan Balance
                        if 'Credit_Utilization' in df.columns and 'Loan_Balance' in df.columns:
                            ax_right.scatter(df['Credit_Utilization'], df['Loan_Balance'], alpha=0.6, color='red')
                            ax_right.set_title('Credit Utilization vs Loan Balance')
                            ax_right.set_xlabel('Credit Utilization')
                            ax_right.set_ylabel('Loan Balance')
                            ax_right.grid(True, alpha=0.3)
                        
                        plt.tight_layout()
                        st.pyplot(fig3)
                    
                    # Payment History Timeline
                    month_cols = [col for col in df.columns if col.startswith('Month_')]
                    if month_cols:
                        st.subheader("📅 Payment History Timeline")
                        fig4, ax = plt.subplots(figsize=(14, 8))
                        
                        # Calculate payment status percentages over time
                        payment_data = []
                        for month in month_cols:
                            status_counts = df[month].value_counts(normalize=True) * 100
                            payment_data.append(status_counts)
                        
                        payment_df = pd.DataFrame(payment_data, index=month_cols)
                        payment_df = payment_df.fillna(0)
                        
                        # Stacked area plot
                        ax.stackplot(range(len(month_cols)), 
                                   payment_df.get('On-time', [0]*len(month_cols)),
                                   payment_df.get('Late', [0]*len(month_cols)),
                                   payment_df.get('Missed', [0]*len(month_cols)),
                                   labels=['On-time', 'Late', 'Missed'],
                                   colors=['green', 'orange', 'red'],
                                   alpha=0.7)
                        
                        ax.set_title('Payment Status Over Time (%)', fontsize=16)
                        ax.set_xlabel('Month')
                        ax.set_ylabel('Percentage')
                        ax.set_xticks(range(len(month_cols)))
                        ax.set_xticklabels(month_cols, rotation=45)
                        ax.legend(loc='upper right')
                        ax.grid(True, alpha=0.3)
                        
                        plt.tight_layout()
                        st.pyplot(fig4)
                    
                    # Correlation heatmap
                    if len(df.select_dtypes(include=[np.number]).columns) > 1:
                        st.subheader("📈 Correlation Matrix")
                        fig2, ax = plt.subplots(figsize=(12, 8))
                        numeric_cols = df.select_dtypes(include=[np.number]).columns
                        correlation_matrix = df[numeric_cols].corr()
                        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', ax=ax, fmt='.2f')
                        ax.set_title('Correlation Matrix')
                        st.pyplot(fig2)
                    
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