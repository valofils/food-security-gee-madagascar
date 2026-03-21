import pandas as pd


INPUT_PATH = "data/processed/grand_sud_monthly_features_v2.csv"
OUTPUT_PATH = "data/processed/grand_sud_dataset_v2.csv"


def main():
    df = pd.read_csv(INPUT_PATH)

    print("Shape:", df.shape)
    print("\nColumns:", df.columns.tolist())

    if "district_name" in df.columns:
        print("\nDistricts:", df["district_name"].nunique())
    if "date" in df.columns:
        print("Date range:", df["date"].min(), "->", df["date"].max())

    drop_if_exists = [c for c in ["system:index", ".geo"] if c in df.columns]
    if drop_if_exists:
        print("\nDropping helper columns:", drop_if_exists)
        df = df.drop(columns=drop_if_exists)

    print("\nMissing values:")
    print(df.isna().sum())

    summary_cols = [
        "ndvi_mean",
        "rainfall_total_mm",
        "lst_day_mean_c",
        "et_total_mm",
        "ndvi_anomaly",
        "rainfall_anomaly_mm",
    ]
    available_summary_cols = [c for c in summary_cols if c in df.columns]

    if available_summary_cols:
        print("\nSummary:")
        print(df[available_summary_cols].describe())

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved cleaned file: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()