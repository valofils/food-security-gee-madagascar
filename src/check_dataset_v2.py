import pandas as pd

df = pd.read_csv("data/processed/grand_sud_monthly_features_v2.csv")

print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())

print("\nDistricts:", df["district_name"].nunique())
print("Date range:", df["date"].min(), "->", df["date"].max())

drop_if_exists = [c for c in ["system:index", ".geo"] if c in df.columns]
if drop_if_exists:
    print("\nDropping helper columns:", drop_if_exists)
    df = df.drop(columns=drop_if_exists)

print("\nMissing values:")
print(df.isna().sum())

print("\nSummary:")
print(df[[
    "ndvi_mean",
    "rainfall_total_mm",
    "lst_day_mean_c",
    "et_total_mm",
    "ndvi_anomaly",
    "rainfall_anomaly_mm"
]].describe())

df.to_csv("data/processed/grand_sud_dataset_v2.csv", index=False)
print("\nSaved cleaned file: data/processed/grand_sud_dataset_v2.csv")