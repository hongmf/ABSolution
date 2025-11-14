import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

class TimeSeriesPredictor:
    def __init__(self):
        self.models = {
            'linear': LinearRegression(),
            'xgboost': xgb.XGBRegressor(n_estimators=100, random_state=42),
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        self.best_model = None
        self.best_model_name = None
        
    def create_features(self, data, target_col, window=3):
        """Create lag features for time series prediction"""
        df = data.copy()
        
        # Create lag features
        for i in range(1, window + 1):
            df[f'{target_col}_lag_{i}'] = df[target_col].shift(i)
        
        # Create rolling statistics
        df[f'{target_col}_rolling_mean'] = df[target_col].rolling(window=window).mean()
        df[f'{target_col}_rolling_std'] = df[target_col].rolling(window=window).std()
        
        # Create trend feature
        df['trend'] = range(len(df))
        
        return df.dropna()
    
    def prepare_data(self, df, target_col, group_col=None):
        """Prepare data for prediction"""
        results = {}
        
        if group_col and group_col in df.columns:
            # Group by company/issuer
            for group in df[group_col].unique():
                group_data = df[df[group_col] == group].copy()
                if len(group_data) >= 10:  # Minimum data points
                    group_data = group_data.sort_values('filing_date' if 'filing_date' in group_data.columns else group_data.index)
                    results[group] = self.create_features(group_data, target_col)
        else:
            # Single time series
            df_sorted = df.sort_values('filing_date' if 'filing_date' in df.columns else df.index)
            results['All Data'] = self.create_features(df_sorted, target_col)
        
        return results
    
    def train_and_predict(self, data, target_col, prediction_steps=None):
        """Train models and make predictions"""
        if prediction_steps is None:
            prediction_steps = max(1, len(data) // 5)  # 1/5 of data length
        
        # Split data
        train_size = len(data) - prediction_steps
        train_data = data.iloc[:train_size]
        
        # Prepare features
        feature_cols = [col for col in data.columns if col != target_col and col != 'filing_date']
        X_train = train_data[feature_cols]
        y_train = train_data[target_col]
        
        # Train models and select best
        best_score = -np.inf
        
        for name, model in self.models.items():
            try:
                model.fit(X_train, y_train)
                score = model.score(X_train, y_train)
                if score > best_score:
                    best_score = score
                    self.best_model = model
                    self.best_model_name = name
            except:
                continue
        
        # Make predictions
        predictions = []
        current_data = data.iloc[-len(feature_cols):].copy()
        
        for i in range(prediction_steps):
            # Get features for prediction
            X_pred = current_data[feature_cols].iloc[-1:].values.reshape(1, -1)
            pred = self.best_model.predict(X_pred)[0]
            predictions.append(pred)
            
            # Update features for next prediction
            new_row = current_data.iloc[-1].copy()
            new_row[target_col] = pred
            new_row['trend'] += 1
            
            # Update lag features
            for lag in range(1, 4):
                if f'{target_col}_lag_{lag}' in new_row.index:
                    if lag == 1:
                        new_row[f'{target_col}_lag_{lag}'] = current_data[target_col].iloc[-1]
                    else:
                        new_row[f'{target_col}_lag_{lag}'] = current_data[f'{target_col}_lag_{lag-1}'].iloc[-1]
            
            current_data = pd.concat([current_data, new_row.to_frame().T], ignore_index=True)
        
        return predictions, train_size
    
    def plot_predictions(self, data_dict, target_col, predictions_dict, train_sizes):
        """Plot time series with predictions"""
        plt.figure(figsize=(15, 8))
        
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        
        for i, (group, data) in enumerate(data_dict.items()):
            color = colors[i % len(colors)]
            
            # Plot historical data
            plt.plot(range(len(data)), data[target_col], 
                    color=color, label=f'{group} (Historical)', linewidth=2)
            
            # Plot predictions
            if group in predictions_dict:
                predictions = predictions_dict[group]
                train_size = train_sizes[group]
                pred_x = range(train_size, train_size + len(predictions))
                plt.plot(pred_x, predictions, 
                        color=color, linestyle='--', label=f'{group} (Predicted)', linewidth=2)
                
                # Add vertical line to separate historical and predicted
                plt.axvline(x=train_size, color=color, linestyle=':', alpha=0.5)
        
        plt.title(f'{target_col} - Historical vs Predicted', fontsize=16)
        plt.xlabel('Time Period')
        plt.ylabel(target_col)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return plt.gcf()

def predict_time_series(df, target_col, group_col=None):
    """Main function to predict time series"""
    predictor = TimeSeriesPredictor()
    
    # Prepare data
    data_dict = predictor.prepare_data(df, target_col, group_col)
    
    if not data_dict:
        return None, "No suitable data found for prediction"
    
    # Train and predict for each group
    predictions_dict = {}
    train_sizes = {}
    
    for group, data in data_dict.items():
        try:
            predictions, train_size = predictor.train_and_predict(data, target_col)
            predictions_dict[group] = predictions
            train_sizes[group] = train_size
        except Exception as e:
            print(f"Error predicting for {group}: {str(e)}")
            continue
    
    # Plot results
    fig = predictor.plot_predictions(data_dict, target_col, predictions_dict, train_sizes)
    
    # Return summary
    summary = {
        'model_used': predictor.best_model_name,
        'groups_predicted': len(predictions_dict),
        'prediction_length': len(list(predictions_dict.values())[0]) if predictions_dict else 0
    }
    
    return fig, summary