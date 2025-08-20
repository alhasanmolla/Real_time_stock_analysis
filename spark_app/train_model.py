import yfinance as yf
import pandas as pd
import pickle
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# ১. AAPL এর ঐতিহাসিক ডেটা ডাউনলোড
print("📥 Downloading AAPL historical data...")
data = yf.download("AAPL", period="6d", interval="1m")  # শেষ ৬ মাসের ডেইলি ডেটা

# ২. ডেটা প্রসেসিং
data = data.dropna().reset_index()
data.rename(columns={
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume"
}, inplace=True)

# ৩. ফিচার ও টার্গেট তৈরি
# টার্গেট: পরের দিনের close প্রাইস (shift -1)
data["target"] = data["close"].shift(-1)
data = data.dropna()

X = data[["open", "high", "low", "close", "volume"]]
y = data["target"]

# ৪. ডেটা স্প্লিট
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# ৫. মডেল ট্রেইন
print("🤖 Training Linear Regression model...")
model = LinearRegression()
model.fit(X_train, y_train)

# ৬. মডেল পারফরম্যান্স চেক
y_pred = model.predict(X_test)
print(f"📊 R² Score: {r2_score(y_test, y_pred):.4f}")

# ৭. মডেল সেভ
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ model.pkl saved successfully!")
print("✅ Model training completed and saved as model.pkl")