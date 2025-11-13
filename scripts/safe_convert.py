import pandas as pd
import numpy as np

def safe_numeric_conversion(df):
    """Convert columns to numeric where possible, keep as string otherwise"""
    for col in df.columns:
        # Try to convert to numeric, keep original if fails
        df[col] = pd.to_numeric(df[col], errors='ignore')
    return df

# Usage in notebook:
# df = safe_numeric_conversion(df)
# numeric_cols = df.select_dtypes(include=[np.number]).columns