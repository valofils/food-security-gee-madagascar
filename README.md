# 🌵 District-Level Drought Risk Prediction in Southern Madagascar
### Machine Learning + Remote Sensing Early Warning System

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Study Area](#2-study-area)
3. [Data](#3-data)
4. [Drought Definition](#4-drought-definition-target-variable)
5. [Machine Learning Models](#5-machine-learning-models)
6. [Early Warning System Outputs](#6-early-warning-system-outputs)
7. [Dashboard](#7-dashboard)
8. [Project Structure](#8-project-structure)
9. [Key Results](#9-key-results)
10. [Limitations](#10-limitations)
11. [Next Steps](#11-next-steps)
12. [Potential Applications](#12-potential-applications)
13. [Author](#13-author)

---

## 1. Project Overview

This project develops a **district-level early warning system** to predict next-month drought risk in the **Grand Sud of Madagascar** using Earth observation data and machine learning.

**Objectives:**
- 🍽️ Food security early warning
- 🤝 Humanitarian planning
- 🌍 Climate risk monitoring
- 🛡️ Drought preparedness

> The system predicts the **probability of drought for the next month** for each district.

---

## 2. Study Area

The project focuses on the **Grand Sud of Madagascar**, one of the most drought-prone regions in Sub-Saharan Africa.

**Key districts:**

| District | |
|---|---|
| Ambovombe-Androy | Tsihombe |
| Amboasary-Atsimo | Bekily |
| Betioky Atsimo | Taolagnaro |
| Ampanihy Ouest | |

These areas are highly vulnerable to recurrent drought, food insecurity, agricultural shocks, and climate variability.

---

## 3. Data

The dataset is built at **district** spatial level and **monthly** temporal resolution, using remote sensing and climate data.

| Variable | Description |
|---|---|
| NDVI mean | Vegetation index |
| NDVI anomaly | Vegetation anomaly |
| Rainfall total | Monthly rainfall |
| Rainfall anomaly | Rainfall anomaly |
| LST | Land surface temperature |
| Evapotranspiration | Water loss |
| Rainfall lag | Rainfall from previous months |
| NDVI lag | NDVI from previous months |
| Temperature lag | Temperature from previous months |
| Rolling means | 3-month averages |
| Seasonal features | Month sine/cosine |

---

## 4. Drought Definition (Target Variable)

A drought proxy was defined using **environmental anomalies**.

A district-month is classified as **drought** if:

```
Rainfall anomaly < 20th percentile
        OR
NDVI anomaly < 20th percentile
```

The model predicts **drought in the next month (t + 1)**, making it a true **predictive early warning system**.

---

## 5. Machine Learning Models

Two models were tested: **Random Forest** and **Logistic Regression**.

Because drought events are relatively rare, different probability thresholds were tested to balance **precision** (false alarms) and **recall** (missed droughts).

### ✅ Final Selected Model

| Model | Threshold | Precision | Recall | F1-score |
|---|---|---|---|---|
| **Random Forest** | 0.20 | 0.31 | **0.78** | 0.45 |

This model was selected because **recall is critical in early warning systems** — the model detects approximately **78% of drought events**.

---

## 6. Early Warning System Outputs

The system produces for each district-month:

- **Drought risk probability**
- **Drought alert** (if probability > threshold)
- **Alert evaluation:** True Positive · False Positive · False Negative · True Negative

### Output Files

```
outputs/
├── feature_importance_rf.csv
├── model_threshold_comparison.csv
├── drought_alerts_rf_threshold_020.csv
├── district_risk_summary.csv
├── monthly_risk_summary.csv
└── alert_results_detailed.csv
```

---

## 7. Dashboard

A **Streamlit dashboard** was built to visualize:

- Risk over time
- Alerts vs. actual drought
- District risk ranking
- District × Month heatmap
- Top high-risk district-months
- Downloadable alert tables

### Run the Dashboard

```bash
pip install streamlit plotly
streamlit run src/dashboard.py
```

---

## 8. Project Structure

```
food-security-gee-madagascar/
│
├── data/
│
├── outputs/
│   ├── drought_alerts_rf_threshold_020.csv
│   ├── district_risk_summary.csv
│   ├── monthly_risk_summary.csv
│   └── feature_importance_rf.csv
│
├── src/
│   ├── data_processing.py
│   ├── model_training.py
│   ├── inspect_alerts.py
│   └── dashboard.py
│
├── notebooks/
│
├── README.md
└── requirements.txt
```

---

## 9. Key Results

The model identified **high-risk districts consistent with known drought-prone areas** in southern Madagascar.

**Districts with highest predicted drought risk:**

1. 🔴 Taolagnaro
2. 🔴 Amboasary-Atsimo
3. 🔴 Ambovombe-Androy
4. 🟠 Betioky Atsimo
5. 🟠 Benenitra

The model successfully captures **seasonal drought patterns**, **spatial vulnerability**, and **climate anomaly signals** — demonstrating that machine learning can be effective for drought early warning in data-scarce environments.

---

## 10. Limitations

- The drought target is a **proxy** based on NDVI and rainfall anomalies
- The model should be validated with external indicators:
  - SPI / SPEI drought indices
  - IPC food insecurity classification
  - Nutrition data
  - Crop production data

---

## 11. Next Steps

| Priority | Improvement |
|---|---|
| 🔬 Data | Integrate SPI/SPEI drought index |
| 🔬 Data | Add soil moisture data |
| 🔬 Data | Add market price data |
| 🤖 Model | Use XGBoost / LightGBM |
| 🚀 Deployment | Deploy dashboard online |
| ⚙️ Pipeline | Build real-time pipeline using Google Earth Engine |

---

## 12. Potential Applications

This system could be used by:

- 🚨 Early warning systems
- 🤝 NGOs and humanitarian organizations
- 🏛️ Government food security units
- 💰 Climate risk insurance programs
- 🌾 Agricultural planning agencies

---

## 13. Author

**Mariel Andrianavalondrahona**
*Statistician | Data Scientist — Madagascar*

**Fields:** Machine Learning · Remote Sensing · Food Security · Early Warning Systems · Climate Risk Modeling

---

## 🏷️ Keywords

`Drought prediction` `Food security` `Madagascar` `Remote sensing` `NDVI` `Rainfall anomaly` `Machine learning` `Early warning system` `Climate risk` `Random Forest` `Streamlit dashboard`