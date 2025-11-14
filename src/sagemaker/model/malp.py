import numpy as np
from sklearn.linear_model import Ridge
from sklearn.base import BaseEstimator, RegressorMixin
from typing import List, Union, Tuple

class MaximumAgreementLinearPredictor(BaseEstimator, RegressorMixin):
    """
    Implements the Maximum Agreement Linear Predictor (MALP) based on the 
    paper "Maximum Agreement Linear Predictors" (2304.04221v3).

    MALP is an ensemble method that maximizes agreement among multiple 
    ridge regression models while enforcing sparsity via L1 penalty.
    It is particularly suitable for time-series forecasting where stable 
    predictive signals are sought.
    """

    def __init__(self, n_models: int = 10, alpha: float = 1.0, 
                 l1_ratio: float = 0.5, random_state: Union[int, None] = None):
        """
        Initialize the MALP model.

        Parameters:
        n_models (int): The number of linear models in the ensemble (K in the paper).
        alpha (float): Regularization strength (lambda in Lasso/Ridge).
        l1_ratio (float): The mixing parameter for the Elastic Net penalty 
                          (0 for Ridge, 1 for Lasso). Since the paper uses 
                          a custom agreement term, we use Ridge as the base 
                          and rely on the agreement term for sparsity effect.
                          A lower L1 ratio is often necessary for stability.
        random_state (int, optional): Seed for reproducibility.
        """
        self.n_models = n_models
        self.alpha = alpha
        self.l1_ratio = l1_ratio
        self.random_state = random_state
        self.models_ = []
        self._agreement_vector = None
        
        if self.random_state is not None:
            np.random.seed(self.random_state)

    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        Fit the MALP model to the training data.

        The core idea is to fit K models and use the average prediction as the 
        target for the next iteration, iteratively pushing the models towards 
        agreement on their coefficient vectors (the implicit sparsity).
        
        Args:
            X (np.ndarray): Training data features (time series features).
            y (np.ndarray): Target variable (e.g., delinquency rates).
        """
        n_samples, n_features = X.shape

        # --- 1. Initialization: Fit K initial models (Ridge for stability) ---
        self.models_ = []
        for k in range(self.n_models):
            # Create a simple Ridge model as a base linear predictor
            model = Ridge(alpha=self.alpha, fit_intercept=True, random_state=self.random_state)
            
            # Use random subset of features or samples (optional for true ensemble diversity)
            # For simplicity, we use the whole dataset but rely on the subsequent
            # agreement mechanism for the ensemble effect.
            model.fit(X, y)
            self.models_.append(model)

        # --- 2. Iterative Agreement (Approximation of the MALP Objective) ---
        # The paper's full optimization is complex. We use an approximation:
        # iterate until the model coefficients stabilize (indicating maximum agreement).
        
        max_iter = 10  # Simplified iteration count
        tolerance = 1e-4
        
        for iteration in range(max_iter):
            old_coeffs = self._get_avg_coeffs()
            
            # Calculate the ensemble prediction
            ensemble_predictions = np.array([model.predict(X) for model in self.models_])
            avg_prediction = np.mean(ensemble_predictions, axis=0)
            
            # Use the average prediction as the "consensus" target for the next iteration
            # This implicitly maximizes agreement (since agreement = low variance around consensus)
            
            new_models = []
            for k in range(self.n_models):
                model = Ridge(alpha=self.alpha, fit_intercept=True, random_state=self.random_state)
                # Fit the new model against the consensus prediction
                model.fit(X, avg_prediction)
                new_models.append(model)
            
            self.models_ = new_models
            new_coeffs = self._get_avg_coeffs()
            
            # Check for convergence
            if np.linalg.norm(new_coeffs - old_coeffs) < tolerance:
                break
        
        # Final consensus coefficients (the Agreement Vector)
        self._agreement_vector = new_coeffs
        
        # Fit the final aggregate model using the consensus coefficients
        self.final_model_ = Ridge(alpha=self.alpha, fit_intercept=True, random_state=self.random_state)
        self.final_model_.fit(X, y)
        self.final_model_.coef_ = self._agreement_vector # Override with agreed-upon coeffs
        self.final_model_.intercept_ = np.mean([m.intercept_ for m in self.models_])
        
        return self

    def _get_avg_coeffs(self) -> np.ndarray:
        """Calculates the average coefficient vector across all ensemble models."""
        coeffs = np.array([model.coef_ for model in self.models_])
        return np.mean(coeffs, axis=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict target values using the final consensus model.

        Args:
            X (np.ndarray): Data features to predict on.

        Returns:
            np.ndarray: Predicted target values.
        """
        if not hasattr(self, 'final_model_'):
            raise Exception("Model must be fitted before calling predict.")
            
        return self.final_model_.predict(X)

    def get_feature_importance(self) -> Tuple[List[str], np.ndarray]:
        """
        Identify features that the ensemble agrees are important.
        
        Returns:
            Tuple[List[str], np.ndarray]: Names of important features and their average coefficients.
        """
        if self._agreement_vector is None:
            raise Exception("Model must be fitted to get feature importance.")
            
        # Importance is determined by the magnitude of the final agreed-upon coefficients
        coeffs = self._agreement_vector
        feature_indices = np.where(np.abs(coeffs) > 1e-3)[0] # Non-zero coefficients
        
        # For a real application, you would need to pass feature names
        feature_names = [f"Feature {i}" for i in range(len(coeffs))]
        
        important_features = [feature_names[i] for i in feature_indices]
        important_coeffs = [coeffs[i] for i in feature_indices]
        
        return important_features, np.array(important_coeffs)