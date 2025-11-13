import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

class DelinquencyPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_encoders = {}
        self.feature_importance = None
        
    def prepare_data(self, df):
        """Prepare data for prediction"""
        # Create delinquency target from monthly payment data
        payment_cols = [col for col in df.columns if col.startswith('Month_')]
        if payment_cols:
            # Count missed/late payments
            df['delinquent_months'] = df[payment_cols].apply(
                lambda row: sum(1 for x in row if x in ['Missed', 'Late']), axis=1
            )
            # Binary target: delinquent if >2 missed/late payments
            df['is_delinquent'] = (df['delinquent_months'] > 2).astype(int)
        else:
            # Use existing delinquent account column
            df['is_delinquent'] = df.get('Delinquent_Account', 0)
        
        # Select features
        feature_cols = ['Age', 'Income', 'Credit_Score', 'Credit_Utilization', 
                       'Missed_Payments', 'Loan_Balance', 'Debt_to_Income_Ratio', 
                       'Account_Tenure', 'Employment_Status', 'Credit_Card_Type', 'Location']
        
        # Keep only available columns
        available_cols = [col for col in feature_cols if col in df.columns]
        X = df[available_cols].copy()
        y = df['is_delinquent']
        
        # Encode categorical variables
        for col in X.select_dtypes(include=['object']).columns:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                X[col] = self.label_encoders[col].fit_transform(X[col].astype(str))
            else:
                X[col] = self.label_encoders[col].transform(X[col].astype(str))
        
        # Fill missing values
        X = X.fillna(X.median())
        
        return X, y
    
    def train(self, df):
        """Train the model"""
        X, y = self.prepare_data(df)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model.fit(X_train, y_train)
        
        # Calculate accuracy
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return accuracy
    
    def predict_delinquency_rate(self, df):
        """Predict delinquency rate for the dataset"""
        X, _ = self.prepare_data(df)
        predictions = self.model.predict_proba(X)[:, 1]  # Probability of delinquency
        
        return {
            'overall_rate': np.mean(predictions),
            'high_risk_count': np.sum(predictions > 0.7),
            'medium_risk_count': np.sum((predictions > 0.3) & (predictions <= 0.7)),
            'low_risk_count': np.sum(predictions <= 0.3),
            'predictions': predictions
        }
    
    def get_risk_factors(self):
        """Get top risk factors"""
        if self.feature_importance is not None:
            return self.feature_importance.head(5)
        return None

def analyze_delinquency(df):
    """Main function to analyze delinquency"""
    predictor = DelinquencyPredictor()
    
    # Train model
    accuracy = predictor.train(df)
    
    # Get predictions
    results = predictor.predict_delinquency_rate(df)
    
    # Get risk factors
    risk_factors = predictor.get_risk_factors()
    
    return {
        'model_accuracy': accuracy,
        'delinquency_rate': results['overall_rate'],
        'risk_distribution': {
            'high_risk': results['high_risk_count'],
            'medium_risk': results['medium_risk_count'],
            'low_risk': results['low_risk_count']
        },
        'top_risk_factors': risk_factors,
        'predictions': results['predictions']
    }