"""
SageMaker Training Script for ABS Risk Scoring Model
Builds predictive models for issuer risk scoring and delinquency forecasting
"""

import argparse
import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, roc_curve
)
import xgboost as xgb
import lightgbm as lgb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ABSRiskModel:
    """ABS Risk Scoring Model"""

    def __init__(self, model_type='xgboost'):
        """
        Initialize model

        Args:
            model_type: Type of model ('xgboost', 'lightgbm', 'gradient_boosting', 'random_forest')
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.feature_importance = None

    def prepare_features(self, df):
        """
        Prepare features from raw data

        Args:
            df: DataFrame with filing data

        Returns:
            Feature matrix X and target vector y
        """
        logger.info("Preparing features...")

        # Define feature columns
        feature_cols = [
            'delinquency_30_days',
            'delinquency_60_days',
            'delinquency_90_plus_days',
            'cumulative_default_rate',
            'cumulative_loss_rate',
            'weighted_average_fico',
            'weighted_average_ltv',
            'weighted_average_dti',
            'pool_balance_ratio',
            'pool_seasoning_months',
            'credit_enhancement',
            'subordination_level',
            'months_since_origination'
        ]

        # Add asset class one-hot encoding
        asset_class_dummies = pd.get_dummies(df['asset_class'], prefix='asset_class')

        # Combine features
        X = pd.concat([df[feature_cols], asset_class_dummies], axis=1)

        # Create target variable (high risk = 1 if risk score > 0.6)
        y = (df['risk_label'] == 'HIGH_RISK').astype(int)

        # Handle missing values
        X = X.fillna(X.median())

        self.feature_names = X.columns.tolist()
        logger.info(f"Prepared {len(self.feature_names)} features")

        return X, y

    def train(self, X_train, y_train, X_val=None, y_val=None):
        """
        Train the model

        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
        """
        logger.info(f"Training {self.model_type} model...")

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)

        if self.model_type == 'xgboost':
            self.model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='binary:logistic',
                eval_metric='auc',
                random_state=42
            )

            eval_set = [(X_train_scaled, y_train)]
            if X_val is not None:
                eval_set.append((X_val_scaled, y_val))

            self.model.fit(
                X_train_scaled, y_train,
                eval_set=eval_set,
                verbose=False
            )

        elif self.model_type == 'lightgbm':
            self.model = lgb.LGBMClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='binary',
                metric='auc',
                random_state=42
            )

            eval_set = [(X_train_scaled, y_train)]
            if X_val is not None:
                eval_set.append((X_val_scaled, y_val))

            self.model.fit(
                X_train_scaled, y_train,
                eval_set=eval_set,
                verbose=False
            )

        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)

        elif self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X_train_scaled, y_train)

        # Calculate feature importance
        self.feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        logger.info("Training completed")

    def evaluate(self, X_test, y_test):
        """
        Evaluate the model

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Evaluating model...")

        X_test_scaled = self.scaler.transform(X_test)

        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        # Metrics
        metrics = {
            'accuracy': (y_pred == y_test).mean(),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'classification_report': classification_report(y_test, y_pred),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }

        logger.info(f"ROC AUC: {metrics['roc_auc']:.4f}")
        logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
        logger.info("\nClassification Report:")
        logger.info(metrics['classification_report'])

        return metrics

    def predict_risk_score(self, X):
        """
        Predict risk scores

        Args:
            X: Features

        Returns:
            Risk scores (probabilities)
        """
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]

    def save_model(self, model_dir):
        """
        Save model artifacts

        Args:
            model_dir: Directory to save model
        """
        logger.info(f"Saving model to {model_dir}")

        # Save model
        joblib.dump(self.model, os.path.join(model_dir, 'model.joblib'))

        # Save scaler
        joblib.dump(self.scaler, os.path.join(model_dir, 'scaler.joblib'))

        # Save feature names
        with open(os.path.join(model_dir, 'feature_names.json'), 'w') as f:
            json.dump(self.feature_names, f)

        # Save feature importance
        self.feature_importance.to_csv(
            os.path.join(model_dir, 'feature_importance.csv'),
            index=False
        )

        # Save model metadata
        metadata = {
            'model_type': self.model_type,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names
        }
        with open(os.path.join(model_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info("Model saved successfully")

    @staticmethod
    def load_model(model_dir):
        """
        Load model artifacts

        Args:
            model_dir: Directory containing model

        Returns:
            ABSRiskModel instance
        """
        logger.info(f"Loading model from {model_dir}")

        # Load metadata
        with open(os.path.join(model_dir, 'metadata.json'), 'r') as f:
            metadata = json.load(f)

        # Create model instance
        model_obj = ABSRiskModel(model_type=metadata['model_type'])

        # Load model
        model_obj.model = joblib.load(os.path.join(model_dir, 'model.joblib'))

        # Load scaler
        model_obj.scaler = joblib.load(os.path.join(model_dir, 'scaler.joblib'))

        # Load feature names
        with open(os.path.join(model_dir, 'feature_names.json'), 'r') as f:
            model_obj.feature_names = json.load(f)

        logger.info("Model loaded successfully")
        return model_obj


def generate_synthetic_training_data(n_samples=10000):
    """
    Generate synthetic training data for demonstration
    In production, this would use historical SEC filing data
    """
    logger.info(f"Generating {n_samples} synthetic training samples...")

    np.random.seed(42)

    # Asset classes
    asset_classes = np.random.choice(
        ['AUTO_LOAN', 'CREDIT_CARD', 'STUDENT_LOAN', 'MORTGAGE'],
        size=n_samples
    )

    # Generate correlated features
    data = {
        'asset_class': asset_classes,
        'delinquency_30_days': np.random.beta(2, 20, n_samples),
        'delinquency_60_days': np.random.beta(1.5, 25, n_samples),
        'delinquency_90_plus_days': np.random.beta(1, 30, n_samples),
        'cumulative_default_rate': np.random.beta(2, 15, n_samples),
        'cumulative_loss_rate': np.random.beta(1.5, 20, n_samples),
        'weighted_average_fico': np.random.normal(700, 50, n_samples).clip(500, 850),
        'weighted_average_ltv': np.random.beta(6, 3, n_samples),
        'weighted_average_dti': np.random.beta(4, 6, n_samples),
        'pool_balance_ratio': np.random.beta(5, 2, n_samples),
        'pool_seasoning_months': np.random.exponential(24, n_samples).clip(0, 120),
        'credit_enhancement': np.random.beta(3, 7, n_samples) * 0.2,
        'subordination_level': np.random.beta(2, 8, n_samples) * 0.15,
        'months_since_origination': np.random.exponential(18, n_samples).clip(0, 60)
    }

    df = pd.DataFrame(data)

    # Create risk labels based on multiple factors
    risk_score = (
        df['delinquency_90_plus_days'] * 3 +
        df['cumulative_loss_rate'] * 2 +
        (1 - df['weighted_average_fico'] / 850) * 1.5 +
        df['weighted_average_ltv'] * 1 +
        (1 - df['pool_balance_ratio']) * 0.5 +
        np.random.normal(0, 0.1, n_samples)
    )

    # Normalize to 0-1 range
    risk_score = (risk_score - risk_score.min()) / (risk_score.max() - risk_score.min())

    # Create binary labels (high risk if > 0.6)
    df['risk_label'] = np.where(risk_score > 0.6, 'HIGH_RISK', 'LOW_RISK')

    logger.info(f"High risk samples: {(df['risk_label'] == 'HIGH_RISK').sum()}")
    logger.info(f"Low risk samples: {(df['risk_label'] == 'LOW_RISK').sum()}")

    return df


def train_model(args):
    """
    Main training function

    Args:
        args: Command line arguments
    """
    logger.info("Starting model training...")

    # Load or generate training data
    if args.train_data:
        logger.info(f"Loading training data from {args.train_data}")
        df = pd.read_csv(args.train_data)
    else:
        logger.info("Generating synthetic training data")
        df = generate_synthetic_training_data(args.n_samples)

    # Initialize model
    model = ABSRiskModel(model_type=args.model_type)

    # Prepare features
    X, y = model.prepare_features(df)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )

    logger.info(f"Train size: {len(X_train)}")
    logger.info(f"Validation size: {len(X_val)}")
    logger.info(f"Test size: {len(X_test)}")

    # Train model
    model.train(X_train, y_train, X_val, y_val)

    # Evaluate model
    metrics = model.evaluate(X_test, y_test)

    # Save metrics
    with open(os.path.join(args.model_dir, 'metrics.json'), 'w') as f:
        json.dump({
            'accuracy': float(metrics['accuracy']),
            'roc_auc': float(metrics['roc_auc']),
            'confusion_matrix': metrics['confusion_matrix']
        }, f, indent=2)

    # Save model
    model.save_model(args.model_dir)

    logger.info("Training completed successfully")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # Data parameters
    parser.add_argument('--train-data', type=str, default=None,
                       help='Path to training data CSV')
    parser.add_argument('--n-samples', type=int, default=10000,
                       help='Number of synthetic samples to generate')

    # Model parameters
    parser.add_argument('--model-type', type=str, default='xgboost',
                       choices=['xgboost', 'lightgbm', 'gradient_boosting', 'random_forest'],
                       help='Type of model to train')

    # SageMaker parameters
    parser.add_argument('--model-dir', type=str,
                       default=os.environ.get('SM_MODEL_DIR', './model'))
    parser.add_argument('--output-data-dir', type=str,
                       default=os.environ.get('SM_OUTPUT_DATA_DIR', './output'))

    args = parser.parse_args()

    # Create output directories
    os.makedirs(args.model_dir, exist_ok=True)
    os.makedirs(args.output_data_dir, exist_ok=True)

    # Train model
    train_model(args)
