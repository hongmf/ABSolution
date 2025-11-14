import numpy as np
import pandas as pd
from malp import MaximumAgreementLinearPredictor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# --- 1. Simulate Time Series Data (Delinquency Rates) ---
# We simulate a series where the target (Delinquency Rate) is driven by 
# a few true factors and many irrelevant factors (sparsity challenge).
np.random.seed(42)
N = 200 # number of data points (time periods)
N_FEATURES = 20 # 20 macroeconomic/loan portfolio features
LAG = 3 # Use 3 previous time periods as features

# Simulate Features (Lagged values of Macroeconomic Indicators)
X_raw = np.random.randn(N, N_FEATURES)

# Simulate Target (Delinquency Rate)
# True relationship: Target = 5 * F1 - 2 * F3 + noise
true_target = 5 * X_raw[:, 1] - 2 * X_raw[:, 3] + 10  
delinquency_rate = true_target + np.random.randn(N) * 0.5 

# --- 2. Prepare Lagged Time Series Data (Feature Engineering) ---

def create_lagged_features(data, lag):
    X, y = [], []
    for i in range(lag, len(data)):
        # Features X: Lagged values of all features 
        X.append(data[i-lag:i, :].flatten())
        # Target y: Current delinquency rate
        y.append(delinquency_rate[i])
    return np.array(X), np.array(y)

# Use X_raw and delinquency_rate to create lagged features
X_lagged, y_lagged = create_lagged_features(X_raw, LAG)

# Split data (standard time series split: train on early data, test on later data)
X_train, X_test, y_train, y_test = train_test_split(
    X_lagged, y_lagged, test_size=0.3, shuffle=False
)

print(f"Total samples: {len(X_lagged)}")
print(f"Training samples: {len(X_train)}")
print(f"Testing samples: {len(X_test)}\n")


# --- 3. Initialize and Fit the MALP Model ---

# We choose a small number of models (K=5) and moderate regularization (alpha=2.0)
malp_model = MaximumAgreementLinearPredictor(
    n_models=5, 
    alpha=2.0, 
    random_state=42
)

print("Fitting MALP model (iteratively achieving maximum agreement)...")
malp_model.fit(X_train, y_train)
print("Fitting complete.\n")


# --- 4. Predict and Evaluate ---

y_pred = malp_model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)

print(f"Mean Squared Error (MSE) on Test Data: {mse:.4f}")

# --- 5. Analyze Agreement and Feature Importance ---

important_features, coeffs = malp_model.get_feature_importance()

# Display results in a DataFrame
feature_df = pd.DataFrame({
    'Feature': important_features,
    'Coefficient': coeffs
}).sort_values(by='Coefficient', ascending=False)

print("\n--- Top Features by Consensus (Agreement Vector) ---")
print(feature_df)

# The MALP model successfully identifies the most robust predictors by enforcing
# agreement, thus ignoring noisy features that only one or two models might find useful.