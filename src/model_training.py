import os
import warnings
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    recall_score,
    confusion_matrix,
    precision_score,
    f1_score
)

warnings.filterwarnings("ignore")


# ==================================================
# 1. CONFIGURATION
# ==================================================
DATA_PATH = "data/processed/grand_sud_features_final.csv"
OUTPUT_DIR = "outputs"

TRAIN_END_YEAR = 2022
THRESHOLDS = [0.5, 0.3, 0.2, 0.15, 0.1]

FEATURE_IMPORTANCE_PATH = os.path.join(OUTPUT_DIR, "feature_importance_rf.csv")
MODEL_COMPARISON_PATH = os.path.join(OUTPUT_DIR, "model_threshold_comparison.csv")
ALERTS_PATH = os.path.join(OUTPUT_DIR, "drought_alerts_rf_threshold_020.csv")

FINAL_MODEL_NAME = "RandomForest"
FINAL_THRESHOLD = 0.20


# ==================================================
# 2. LOAD DATA
# ==================================================
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH)

print("Initial shape:", df.shape)
print("Columns:", df.columns.tolist())


# ==================================================
# 3. CHECK REQUIRED COLUMNS
# ==================================================
required_columns = [
    "district_id",
    "district_name",
    "year",
    "month",
    "ndvi_mean",
    "rainfall_total_mm",
    "lst_day_mean_c",
    "et_total_mm",
    "ndvi_anomaly",
    "rainfall_anomaly_mm",
    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "ndvi_lag_1",
    "ndvi_lag_2",
    "ndvi_lag_3",
    "temp_lag_1",
    "temp_lag_2",
    "temp_lag_3",
    "rain_3m_mean",
    "ndvi_3m_mean",
    "month_sin",
    "month_cos"
]

missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")


# ==================================================
# 4. SORT DATA
# ==================================================
df = df.sort_values(["district_id", "year", "month"]).reset_index(drop=True)


# ==================================================
# 5. CREATE PROXY DROUGHT LABEL
#    Rule:
#    drought = 1 if rainfall anomaly OR NDVI anomaly
#    is in the lowest 20%
# ==================================================
rain_thresh = df["rainfall_anomaly_mm"].quantile(0.20)
ndvi_thresh = df["ndvi_anomaly"].quantile(0.20)

print("\nDrought thresholds:")
print(f"Rainfall anomaly threshold (20th percentile): {rain_thresh:.4f}")
print(f"NDVI anomaly threshold (20th percentile): {ndvi_thresh:.4f}")

df["drought"] = (
    (df["rainfall_anomaly_mm"] <= rain_thresh) |
    (df["ndvi_anomaly"] <= ndvi_thresh)
).astype(int)

print("\nCurrent-month drought distribution:")
print(df["drought"].value_counts(normalize=True))


# ==================================================
# 6. ADD EXTRA ROLLING FEATURES
# ==================================================
df["rain_6m_mean"] = (
    df.groupby("district_id")["rainfall_total_mm"]
    .transform(lambda x: x.rolling(6, min_periods=1).mean())
)

df["ndvi_6m_mean"] = (
    df.groupby("district_id")["ndvi_mean"]
    .transform(lambda x: x.rolling(6, min_periods=1).mean())
)

df["temp_3m_mean"] = (
    df.groupby("district_id")["lst_day_mean_c"]
    .transform(lambda x: x.rolling(3, min_periods=1).mean())
)

df["temp_6m_mean"] = (
    df.groupby("district_id")["lst_day_mean_c"]
    .transform(lambda x: x.rolling(6, min_periods=1).mean())
)


# ==================================================
# 7. CREATE NEXT-MONTH TARGET
# ==================================================
df["drought_next"] = df.groupby("district_id")["drought"].shift(-1)

df = df.dropna(subset=["drought_next"]).copy()
df["drought_next"] = df["drought_next"].astype(int)

print("\nNext-month drought distribution:")
print(df["drought_next"].value_counts(normalize=True))


# ==================================================
# 8. DEFINE FEATURES
# ==================================================
features = [
    "ndvi_mean",
    "rainfall_total_mm",
    "lst_day_mean_c",
    "et_total_mm",
    "ndvi_anomaly",
    "rainfall_anomaly_mm",
    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "ndvi_lag_1",
    "ndvi_lag_2",
    "ndvi_lag_3",
    "temp_lag_1",
    "temp_lag_2",
    "temp_lag_3",
    "rain_3m_mean",
    "ndvi_3m_mean",
    "rain_6m_mean",
    "ndvi_6m_mean",
    "temp_3m_mean",
    "temp_6m_mean",
    "month_sin",
    "month_cos"
]

df = df.dropna(subset=features + ["drought_next"]).copy()


# ==================================================
# 9. TRAIN / TEST SPLIT
# ==================================================
train = df[df["year"] <= TRAIN_END_YEAR].copy()
test = df[df["year"] > TRAIN_END_YEAR].copy()

if len(train) == 0 or len(test) == 0:
    raise ValueError("Train or test set is empty. Check the year split.")

X_train = train[features]
y_train = train["drought_next"]

X_test = test[features]
y_test = test["drought_next"]

print("\nTrain size:", X_train.shape)
print("Test size:", X_test.shape)

print("\nTrain target distribution:")
print(y_train.value_counts(normalize=True))

print("\nTest target distribution:")
print(y_test.value_counts(normalize=True))


# ==================================================
# 10. DEFINE MODELS
# ==================================================
models = {
    "RandomForest": RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        class_weight="balanced",
        random_state=42
    ),
    "LogisticRegression": LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42
    )
}


# ==================================================
# 11. EVALUATION FUNCTION
# ==================================================
def evaluate_thresholds(model_name, model, X_test, y_test, thresholds):
    y_prob = model.predict_proba(X_test)[:, 1]
    results = []

    print(f"\n{'=' * 60}")
    print(f"MODEL: {model_name}")
    print(f"{'=' * 60}")

    for threshold in thresholds:
        y_pred = (y_prob >= threshold).astype(int)

        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)

        print(f"\n---------- Threshold = {threshold} ----------")
        print(classification_report(y_test, y_pred, zero_division=0))
        print("Confusion matrix:")
        print(cm)
        print(f"Precision (class 1): {precision:.4f}")
        print(f"Recall    (class 1): {recall:.4f}")
        print(f"F1-score  (class 1): {f1:.4f}")

        results.append({
            "model": model_name,
            "threshold": threshold,
            "precision_class_1": precision,
            "recall_class_1": recall,
            "f1_class_1": f1,
            "tn": int(cm[0, 0]),
            "fp": int(cm[0, 1]),
            "fn": int(cm[1, 0]),
            "tp": int(cm[1, 1])
        })

    return pd.DataFrame(results)


# ==================================================
# 12. TRAIN AND EVALUATE ALL MODELS
# ==================================================
all_results = []
trained_models = {}

for model_name, model in models.items():
    print(f"\nTraining {model_name}...")
    model.fit(X_train, y_train)
    trained_models[model_name] = model

    result_df = evaluate_thresholds(
        model_name=model_name,
        model=model,
        X_test=X_test,
        y_test=y_test,
        thresholds=THRESHOLDS
    )
    all_results.append(result_df)

    if model_name == "RandomForest":
        importance = pd.Series(model.feature_importances_, index=features)
        importance = importance.sort_values(ascending=False)

        print("\nTop 10 Random Forest feature importances:")
        print(importance.head(10))

        importance.to_csv(FEATURE_IMPORTANCE_PATH, header=["importance"])
        print(f"\nFeature importance saved to: {FEATURE_IMPORTANCE_PATH}")


# ==================================================
# 13. SAVE MODEL COMPARISON RESULTS
# ==================================================
results_df = pd.concat(all_results, ignore_index=True)
results_df.to_csv(MODEL_COMPARISON_PATH, index=False)
print(f"\nModel comparison results saved to: {MODEL_COMPARISON_PATH}")


# ==================================================
# 14. SHOW BEST CONFIGURATIONS
# ==================================================
best_by_recall = results_df.sort_values(
    by=["recall_class_1", "f1_class_1", "precision_class_1"],
    ascending=False
).head(5)

print("\nTop 5 configurations by recall for drought (class 1):")
print(best_by_recall)


# ==================================================
# 15. SAVE FINAL ALERT TABLE
#    Recommended baseline:
#    RandomForest at threshold 0.20
# ==================================================
final_model = trained_models[FINAL_MODEL_NAME]
final_y_prob = final_model.predict_proba(X_test)[:, 1]
final_y_pred = (final_y_prob >= FINAL_THRESHOLD).astype(int)

alerts = test[["district_id", "district_name", "year", "month"]].copy()
alerts["drought_next_actual"] = y_test.values
alerts["drought_risk_prob"] = final_y_prob
alerts["drought_alert"] = final_y_pred

alerts.to_csv(ALERTS_PATH, index=False)
print(f"\nAlert table saved to: {ALERTS_PATH}")


# ==================================================
# 16. FINAL SUMMARY
# ==================================================
final_precision = precision_score(y_test, final_y_pred, zero_division=0)
final_recall = recall_score(y_test, final_y_pred, zero_division=0)
final_f1 = f1_score(y_test, final_y_pred, zero_division=0)
final_cm = confusion_matrix(y_test, final_y_pred)

print(f"\nFinal selected model: {FINAL_MODEL_NAME}")
print(f"Final threshold: {FINAL_THRESHOLD}")
print(f"Final precision (class 1): {final_precision:.4f}")
print(f"Final recall    (class 1): {final_recall:.4f}")
print(f"Final F1-score  (class 1): {final_f1:.4f}")
print("Final confusion matrix:")
print(final_cm)

print("\nModel training complete.")