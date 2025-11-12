"""
SageMaker Inference Script for ABS Risk Model
Handles model serving and predictions
"""

import json
import joblib
import numpy as np
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables to hold model artifacts
model = None
scaler = None
feature_names = None


def model_fn(model_dir):
    """
    Load the model for inference

    Args:
        model_dir: Directory where model artifacts are stored

    Returns:
        Dictionary containing model, scaler, and feature names
    """
    global model, scaler, feature_names

    logger.info(f"Loading model from {model_dir}")

    try:
        # Load model
        model = joblib.load(os.path.join(model_dir, 'model.joblib'))

        # Load scaler
        scaler = joblib.load(os.path.join(model_dir, 'scaler.joblib'))

        # Load feature names
        with open(os.path.join(model_dir, 'feature_names.json'), 'r') as f:
            feature_names = json.load(f)

        logger.info(f"Model loaded successfully with {len(feature_names)} features")

        return {
            'model': model,
            'scaler': scaler,
            'feature_names': feature_names
        }

    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise


def input_fn(request_body, content_type='application/json'):
    """
    Deserialize and prepare the input data

    Args:
        request_body: The request body
        content_type: The content type of the request

    Returns:
        Input data as numpy array
    """
    logger.info(f"Processing input with content_type: {content_type}")

    if content_type == 'application/json':
        input_data = json.loads(request_body)

        # Handle different input formats
        if 'instances' in input_data:
            # Batch prediction format
            instances = input_data['instances']
            return np.array(instances)

        elif 'features' in input_data:
            # Single prediction with named features
            features = input_data['features']
            feature_vector = [features.get(name, 0) for name in feature_names]
            return np.array([feature_vector])

        elif isinstance(input_data, list):
            # Direct list of feature values
            return np.array([input_data])

        else:
            raise ValueError("Invalid input format")

    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data, model_artifacts):
    """
    Make predictions on the input data

    Args:
        input_data: Input data as numpy array
        model_artifacts: Dictionary containing model, scaler, feature_names

    Returns:
        Predictions
    """
    logger.info(f"Making predictions for {len(input_data)} instances")

    try:
        # Extract artifacts
        model = model_artifacts['model']
        scaler = model_artifacts['scaler']

        # Scale features
        input_scaled = scaler.transform(input_data)

        # Make predictions
        predictions = model.predict(input_scaled)
        probabilities = model.predict_proba(input_scaled)

        # Return predictions with confidence scores
        results = []
        for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
            risk_score = float(proba[1])  # Probability of high risk
            risk_level = categorize_risk(risk_score)

            results.append({
                'prediction': int(pred),
                'risk_score': risk_score,
                'risk_level': risk_level,
                'confidence': float(max(proba))
            })

        return results

    except Exception as e:
        logger.error(f"Error making predictions: {str(e)}")
        raise


def categorize_risk(score):
    """Categorize risk score into levels"""
    if score >= 0.75:
        return 'CRITICAL'
    elif score >= 0.60:
        return 'HIGH'
    elif score >= 0.40:
        return 'MEDIUM'
    elif score >= 0.20:
        return 'LOW'
    else:
        return 'MINIMAL'


def output_fn(prediction, accept='application/json'):
    """
    Serialize the prediction output

    Args:
        prediction: The prediction result
        accept: The desired content type

    Returns:
        Serialized output
    """
    if accept == 'application/json':
        return json.dumps({
            'predictions': prediction
        }), accept
    else:
        raise ValueError(f"Unsupported accept type: {accept}")
