import math
import pandas as pd


INPUT_PATH = "data/processed/grand_sud_dataset_v2.csv"
OUTPUT_PATH = "data/processed/grand_sud_features_final.csv"


def main():
    df = pd.read_csv(INPUT_PATH)

    df = df.sort_values(["district_id", "date"]).copy()

    lags = [1, 2, 3]
    for lag in lags:
        df[f"rain_lag_{lag}"] = df.groupby("district_id")["rainfall_total_mm"].shift(lag)
        df[f"ndvi_lag_{lag}"] = df.groupby("district_id")["ndvi_mean"].shift(lag)
        df[f"temp_lag_{lag}"] = df.groupby("district_id")["lst_day_mean_c"].shift(lag)

    df["rain_3m_mean"] = (
        df.groupby("district_id")["rainfall_total_mm"]
        .transform(lambda x: x.rolling(3, min_periods=3).mean())
    )

    df["ndvi_3m_mean"] = (
        df.groupby("district_id")["ndvi_mean"]
        .transform(lambda x: x.rolling(3, min_periods=3).mean())
    )

    df["month_sin"] = pd.to_numeric(df["month"]).apply(
        lambda x: math.sin(2 * math.pi * x / 12)
    )
    df["month_cos"] = pd.to_numeric(df["month"]).apply(
        lambda x: math.cos(2 * math.pi * x / 12)
    )

    df = df.dropna().copy()

    df.to_csv(OUTPUT_PATH, index=False)

    print("Final dataset shape:", df.shape)
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()