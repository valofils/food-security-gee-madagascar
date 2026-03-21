import pandas as pd

df = pd.read_csv("data/processed/grand_sud_dataset_v2.csv")

# Sort panel properly
df = df.sort_values(["district_id", "date"])

# --------------------------------------------------
# 1. Lag features (VERY important)
# --------------------------------------------------
lags = [1, 2, 3]

for lag in lags:
    df[f"rain_lag_{lag}"] = df.groupby("district_id")["rainfall_total_mm"].shift(lag)
    df[f"ndvi_lag_{lag}"] = df.groupby("district_id")["ndvi_mean"].shift(lag)
    df[f"temp_lag_{lag}"] = df.groupby("district_id")["lst_day_mean_c"].shift(lag)

# --------------------------------------------------
# 2. Rolling means (trend / smoothing)
# --------------------------------------------------
df["rain_3m_mean"] = df.groupby("district_id")["rainfall_total_mm"].transform(lambda x: x.rolling(3).mean())
df["ndvi_3m_mean"] = df.groupby("district_id")["ndvi_mean"].transform(lambda x: x.rolling(3).mean())

# --------------------------------------------------
# 3. Seasonal encoding
# --------------------------------------------------
df["month_sin"] = pd.to_numeric(df["month"]).apply(lambda x: __import__("math").sin(2 * 3.1416 * x / 12))
df["month_cos"] = pd.to_numeric(df["month"]).apply(lambda x: __import__("math").cos(2 * 3.1416 * x / 12))

# --------------------------------------------------
# 4. Drop rows with NaN from lags
# --------------------------------------------------
df = df.dropna()

# --------------------------------------------------
# 5. Save
# --------------------------------------------------
df.to_csv("data/processed/grand_sud_features_final.csv", index=False)

print("Final dataset shape:", df.shape)
print("Saved: grand_sud_features_final.csv")