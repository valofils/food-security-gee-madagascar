import os
import pandas as pd


# ==================================================
# CONFIG
# ==================================================
ALERTS_PATH = "outputs/drought_alerts_rf_threshold_020.csv"
OUTPUT_DIR = "outputs"
TOP_N = 20


def main():
    if not os.path.exists(ALERTS_PATH):
        raise FileNotFoundError(f"Alert file not found: {ALERTS_PATH}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = pd.read_csv(ALERTS_PATH)

    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())

    required_columns = [
        "district_id",
        "district_name",
        "year",
        "month",
        "drought_next_actual",
        "drought_risk_prob",
        "drought_alert",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df_sorted = df.sort_values(
        by=["drought_risk_prob", "year", "month"],
        ascending=[False, True, True],
    ).reset_index(drop=True)

    print("\nTop high-risk district-months:")
    print(df_sorted.head(TOP_N).to_string(index=False))

    top_risk = df_sorted.head(TOP_N).copy()
    top_risk_path = os.path.join(OUTPUT_DIR, "top_high_risk_district_months.csv")
    top_risk.to_csv(top_risk_path, index=False)
    print(f"\nSaved top {TOP_N} high-risk district-months to: {top_risk_path}")

    district_summary = (
        df.groupby(["district_id", "district_name"], as_index=False)
        .agg(
            avg_risk_prob=("drought_risk_prob", "mean"),
            max_risk_prob=("drought_risk_prob", "max"),
            n_alerts=("drought_alert", "sum"),
            n_months=("drought_alert", "count"),
            actual_drought_months=("drought_next_actual", "sum"),
        )
    )

    district_summary["alert_rate"] = (
        district_summary["n_alerts"] / district_summary["n_months"]
    )
    district_summary["actual_drought_rate"] = (
        district_summary["actual_drought_months"] / district_summary["n_months"]
    )

    district_summary = district_summary.sort_values(
        by=["avg_risk_prob", "max_risk_prob"],
        ascending=False,
    ).reset_index(drop=True)

    print("\nDistricts with highest average risk:")
    print(district_summary.head(15).to_string(index=False))

    district_summary_path = os.path.join(OUTPUT_DIR, "district_risk_summary.csv")
    district_summary.to_csv(district_summary_path, index=False)
    print(f"\nSaved district summary to: {district_summary_path}")

    monthly_summary = (
        df.groupby(["year", "month"], as_index=False)
        .agg(
            avg_risk_prob=("drought_risk_prob", "mean"),
            max_risk_prob=("drought_risk_prob", "max"),
            n_alerts=("drought_alert", "sum"),
            n_districts=("district_id", "count"),
            actual_drought_months=("drought_next_actual", "sum"),
        )
    )

    monthly_summary["alert_share"] = (
        monthly_summary["n_alerts"] / monthly_summary["n_districts"]
    )
    monthly_summary["actual_drought_share"] = (
        monthly_summary["actual_drought_months"] / monthly_summary["n_districts"]
    )

    monthly_summary = monthly_summary.sort_values(["year", "month"]).reset_index(drop=True)

    print("\nMonthly summary:")
    print(monthly_summary.tail(12).to_string(index=False))

    monthly_summary_path = os.path.join(OUTPUT_DIR, "monthly_risk_summary.csv")
    monthly_summary.to_csv(monthly_summary_path, index=False)
    print(f"\nSaved monthly summary to: {monthly_summary_path}")

    alerts_only = df[df["drought_alert"] == 1].copy()
    alerts_only = alerts_only.sort_values(
        by=["drought_risk_prob", "year", "month"],
        ascending=[False, True, True],
    ).reset_index(drop=True)

    alerts_only_path = os.path.join(OUTPUT_DIR, "all_triggered_alerts.csv")
    alerts_only.to_csv(alerts_only_path, index=False)

    print(f"\nSaved all triggered alerts to: {alerts_only_path}")
    print(f"Total triggered alerts: {len(alerts_only)}")

    df["alert_result"] = "TN"
    df.loc[
        (df["drought_alert"] == 1) & (df["drought_next_actual"] == 1),
        "alert_result",
    ] = "TP"
    df.loc[
        (df["drought_alert"] == 1) & (df["drought_next_actual"] == 0),
        "alert_result",
    ] = "FP"
    df.loc[
        (df["drought_alert"] == 0) & (df["drought_next_actual"] == 1),
        "alert_result",
    ] = "FN"

    result_counts = df["alert_result"].value_counts()
    print("\nAlert result counts:")
    print(result_counts)

    results_path = os.path.join(OUTPUT_DIR, "alert_results_detailed.csv")
    df.to_csv(results_path, index=False)

    print(f"\nSaved detailed alert results to: {results_path}")
    print("\nInspection complete.")


if __name__ == "__main__":
    main()