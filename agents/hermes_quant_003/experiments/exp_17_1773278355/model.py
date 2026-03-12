import json
import pickle
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import os

# Load data
data_path = os.environ.get("DATA_PATH")
if not data_path:
    raise ValueError("DATA_PATH environment variable not set")

data = json.loads(data_path)
features_list = data.get("features", [])

# Convert to DataFrame
df = pd.DataFrame(features_list)

# Extract numerical features
numeric_features = []
for feat in ["price", "volume", "sentiment_score", "title_length", "description_length"]:
    if feat in df.columns:
        numeric_features.append(feat)

df_num = df[numeric_features].fillna(0)

# Create target: next period price change (placeholder)
df_num["target"] = df_num["price"].pct_change().shift(-1)
df_num = df_num.dropna()

# Prepare features and target
X = df_num[numeric_features]
y = df_num["target"]

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Train model
model = XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42
)

model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Calculate PnL (simplified)
initial_capital = 10000
position_size = 0.05  # 5% per trade
capital = initial_capital

trades = []
for i, pred in enumerate(y_pred):
    trade_size = capital * position_size
    actual_return = y_test.iloc[i]
    trade_pnl = trade_size * actual_return
    capital += trade_pnl
    trades.append({
        "pred": pred,
        "actual": actual_return,
        "pnl": trade_pnl
    })

# Calculate metrics
total_pnl = capital - initial_capital
returns = [t["pnl"] / 10000 for t in trades]
sharpe_ratio = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
win_rate = sum(1 for t in trades if t["pnl"] > 0) / len(trades)
cumulative_returns = np.cumsum(returns)
max_drawdown = (np.max(cumulative_returns) - np.min(cumulative_returns))
test_mse = mean_squared_error(y_test, y_pred)

# Save model
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

# Save results
results = {
    "total_pnl": total_pnl,
    "sharpe_ratio": sharpe_ratio,
    "win_rate": win_rate,
    "max_drawdown": max_drawdown,
    "num_trades": len(trades),
    "test_accuracy": 1 - test_mse
}

with open("results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Training complete. PnL: ${total_pnl:.2f}, Sharpe: {sharpe_ratio:.2f}")
