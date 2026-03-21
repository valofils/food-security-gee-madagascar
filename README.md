District-Level Drought Risk Prediction in Southern Madagascar

Machine Learning + Remote Sensing Early Warning System

1. Project Overview

This project develops a district-level early warning system to predict next-month drought risk in the Grand Sud of Madagascar using Earth observation data and machine learning.

The objective is to support:

Food security early warning
Humanitarian planning
Climate risk monitoring
Drought preparedness

The system predicts the probability of drought for the next month for each district.

2. Study Area

The project focuses on the Grand Sud of Madagascar, one of the most drought-prone regions in Sub-Saharan Africa.

Key districts include:

Ambovombe-Androy
Amboasary-Atsimo
Betioky Atsimo
Ampanihy Ouest
Tsihombe
Bekily
Taolagnaro

These areas are highly vulnerable to:

Recurrent drought
Food insecurity
Agricultural shocks
Climate variability

3. Data

The dataset is built at:

Spatial level: District
Temporal level: Monthly
Type: Remote sensing and climate data
Variables used

| Variable           | Description                      |
| ------------------ | -------------------------------- |
| NDVI mean          | Vegetation index                 |
| NDVI anomaly       | Vegetation anomaly               |
| Rainfall total     | Monthly rainfall                 |
| Rainfall anomaly   | Rainfall anomaly                 |
| LST                | Land surface temperature         |
| Evapotranspiration | Water loss                       |
| Rainfall lag       | Rainfall from previous months    |
| NDVI lag           | NDVI from previous months        |
| Temperature lag    | Temperature from previous months |
| Rolling means      | 3-month averages                 |
| Seasonal features  | Month sine/cosine                |

4. Drought Definition (Target Variable)

A drought proxy was defined using environmental anomalies:

A district-month is classified as drought if:

Rainfall anomaly < 20th percentile
OR
NDVI anomaly < 20th percentile

The model predicts:

Drought in the next month (t + 1)

This makes the system a predictive early warning model.

5. Machine Learning Models

Two models were tested:

Random Forest
Logistic Regression

Because drought events are relatively rare, different probability thresholds were tested to balance:

Precision (false alarms)
Recall (missed droughts)
Final selected model
| Model         | Threshold | Precision | Recall | F1-score |
| ------------- | --------- | --------- | ------ | -------- |
| Random Forest | 0.20      | 0.31      | 0.78   | 0.45     |

This model was selected because recall is very important in early warning systems.

The model detects about 78% of drought events.

6. Early Warning System Outputs

The system produces:

Drought risk probability
Drought alert (if probability > threshold)
Alert evaluation:
True Positive (correct alert)
False Positive (false alarm)
False Negative (missed drought)
True Negative
Output files

outputs/
    feature_importance_rf.csv
    model_threshold_comparison.csv
    drought_alerts_rf_threshold_020.csv
    district_risk_summary.csv
    monthly_risk_summary.csv
    alert_results_detailed.csv

7. Dashboard

A Streamlit dashboard was built to visualize:

Risk over time
Alerts vs actual drought
District risk ranking
District × Month heatmap
Top high-risk district-months
Downloadable alert tables
Run the dashboard

pip install streamlit plotly
streamlit run src/dashboard.py

8. Project Structure

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

9. Key Results

The model identified high-risk districts consistent with known drought-prone areas in southern Madagascar.

Districts with highest predicted drought risk:

Taolagnaro
Amboasary-Atsimo
Ambovombe-Androy
Betioky Atsimo
Benenitra

The model captures:

Seasonal drought patterns
Spatial vulnerability
Climate anomaly signals

This shows that machine learning can be used for drought early warning in data-scarce environments.

10. Limitations

Current limitations:

The drought target is a proxy based on NDVI and rainfall anomalies
The model should be validated with external indicators such as:
SPI / SPEI drought indices
IPC food insecurity classification
Nutrition data
Crop production data

11. Next Steps

Future improvements:

Integrate SPI/SPEI drought index
Add soil moisture data
Add market price data
Use XGBoost / LightGBM
Deploy dashboard online
Build real-time pipeline using Google Earth Engine


12. Potential Applications

This system could be used by:

Early warning systems
NGOs
Government food security units
Climate risk insurance programs
Agricultural planning agencies

13. Author

Mariel Andrianavalondrahona
Statistician | Data Scientist
Madagascar

Fields:

Machine Learning
Remote Sensing
Food Security
Early Warning Systems
Climate Risk Modeling


14. Keywords

Drought prediction, Food security, Madagascar, Remote sensing, NDVI, Rainfall anomaly, Machine learning, Early warning system, Climate risk, Random Forest, Streamlit dashboard