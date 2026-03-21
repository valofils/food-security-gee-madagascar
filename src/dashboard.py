import os
import pandas as pd
import streamlit as st
import plotly.express as px

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="Grand Sud Drought Risk Dashboard",
    layout="wide"
)

st.title("Grand Sud Madagascar - Drought Risk Dashboard")
st.caption("Prototype early warning dashboard based on district-level monthly drought risk predictions.")


# ==================================================
# PATHS
# ==================================================
ALERTS_PATH = "outputs/drought_alerts_rf_threshold_020.csv"
DISTRICT_SUMMARY_PATH = "outputs/district_risk_summary.csv"
MONTHLY_SUMMARY_PATH = "outputs/monthly_risk_summary.csv"


# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data
def load_data():
    if not os.path.exists(ALERTS_PATH):
        raise FileNotFoundError(f"Missing file: {ALERTS_PATH}")
    if not os.path.exists(DISTRICT_SUMMARY_PATH):
        raise FileNotFoundError(f"Missing file: {DISTRICT_SUMMARY_PATH}")
    if not os.path.exists(MONTHLY_SUMMARY_PATH):
        raise FileNotFoundError(f"Missing file: {MONTHLY_SUMMARY_PATH}")

    alerts = pd.read_csv(ALERTS_PATH)
    district_summary = pd.read_csv(DISTRICT_SUMMARY_PATH)
    monthly_summary = pd.read_csv(MONTHLY_SUMMARY_PATH)

    alerts["year"] = alerts["year"].astype(int)
    alerts["month"] = alerts["month"].astype(int)
    alerts["year_month"] = pd.to_datetime(
        alerts["year"].astype(str) + "-" + alerts["month"].astype(str).str.zfill(2) + "-01"
    )

    monthly_summary["year"] = monthly_summary["year"].astype(int)
    monthly_summary["month"] = monthly_summary["month"].astype(int)
    monthly_summary["year_month"] = pd.to_datetime(
        monthly_summary["year"].astype(str) + "-" + monthly_summary["month"].astype(str).str.zfill(2) + "-01"
    )

    return alerts, district_summary, monthly_summary


try:
    alerts_df, district_df, monthly_df = load_data()
except Exception as e:
    st.error(str(e))
    st.stop()


# ==================================================
# SIDEBAR FILTERS
# ==================================================
st.sidebar.header("Filters")

districts = sorted(alerts_df["district_name"].dropna().unique().tolist())
years = sorted(alerts_df["year"].dropna().unique().tolist())

selected_districts = st.sidebar.multiselect(
    "Select district(s)",
    options=districts,
    default=districts
)

selected_years = st.sidebar.multiselect(
    "Select year(s)",
    options=years,
    default=years
)

risk_min, risk_max = float(alerts_df["drought_risk_prob"].min()), float(alerts_df["drought_risk_prob"].max())
selected_risk_range = st.sidebar.slider(
    "Risk probability range",
    min_value=0.0,
    max_value=1.0,
    value=(max(0.0, round(risk_min, 2)), min(1.0, round(risk_max, 2))),
    step=0.01
)

show_only_alerts = st.sidebar.checkbox("Show only triggered alerts", value=False)


# ==================================================
# APPLY FILTERS
# ==================================================
filtered_alerts = alerts_df[
    (alerts_df["district_name"].isin(selected_districts)) &
    (alerts_df["year"].isin(selected_years)) &
    (alerts_df["drought_risk_prob"] >= selected_risk_range[0]) &
    (alerts_df["drought_risk_prob"] <= selected_risk_range[1])
].copy()

if show_only_alerts:
    filtered_alerts = filtered_alerts[filtered_alerts["drought_alert"] == 1].copy()

if filtered_alerts.empty:
    st.warning("No data available for the selected filters.")
    st.stop()


# ==================================================
# KPI CARDS
# ==================================================
total_rows = len(filtered_alerts)
avg_risk = filtered_alerts["drought_risk_prob"].mean()
max_risk = filtered_alerts["drought_risk_prob"].max()
n_alerts = int(filtered_alerts["drought_alert"].sum())
n_actual = int(filtered_alerts["drought_next_actual"].sum())

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("District-months", f"{total_rows}")
col2.metric("Average risk", f"{avg_risk:.2f}")
col3.metric("Maximum risk", f"{max_risk:.2f}")
col4.metric("Triggered alerts", f"{n_alerts}")
col5.metric("Actual drought months", f"{n_actual}")


# ==================================================
# 1. RISK OVER TIME
# ==================================================
st.subheader("1. Average drought risk over time")

time_series = (
    filtered_alerts.groupby("year_month", as_index=False)
    .agg(
        avg_risk_prob=("drought_risk_prob", "mean"),
        n_alerts=("drought_alert", "sum"),
        actual_drought=("drought_next_actual", "sum")
    )
)

fig_time = px.line(
    time_series,
    x="year_month",
    y="avg_risk_prob",
    markers=True,
    title="Average drought risk probability by month"
)
fig_time.update_layout(xaxis_title="Month", yaxis_title="Average risk probability")
st.plotly_chart(fig_time, use_container_width=True)


# ==================================================
# 2. ALERTS OVER TIME
# ==================================================
st.subheader("2. Alerts and actual drought over time")

fig_alerts = px.bar(
    time_series,
    x="year_month",
    y=["n_alerts", "actual_drought"],
    barmode="group",
    title="Triggered alerts vs actual drought months"
)
fig_alerts.update_layout(xaxis_title="Month", yaxis_title="Count")
st.plotly_chart(fig_alerts, use_container_width=True)


# ==================================================
# 3. DISTRICT RANKING
# ==================================================
st.subheader("3. District ranking by average risk")

district_ranking = (
    filtered_alerts.groupby("district_name", as_index=False)
    .agg(
        avg_risk_prob=("drought_risk_prob", "mean"),
        max_risk_prob=("drought_risk_prob", "max"),
        n_alerts=("drought_alert", "sum"),
        actual_drought=("drought_next_actual", "sum")
    )
    .sort_values("avg_risk_prob", ascending=False)
)

fig_district = px.bar(
    district_ranking,
    x="district_name",
    y="avg_risk_prob",
    hover_data=["max_risk_prob", "n_alerts", "actual_drought"],
    title="Average drought risk by district"
)
fig_district.update_layout(xaxis_title="District", yaxis_title="Average risk probability")
st.plotly_chart(fig_district, use_container_width=True)


# ==================================================
# 4. HEATMAP: DISTRICT x TIME
# ==================================================
st.subheader("4. Risk heatmap by district and month")

heatmap_df = (
    filtered_alerts.pivot_table(
        index="district_name",
        columns="year_month",
        values="drought_risk_prob",
        aggfunc="mean"
    )
    .sort_index()
)

fig_heatmap = px.imshow(
    heatmap_df,
    aspect="auto",
    title="District-month drought risk heatmap",
    labels=dict(x="Month", y="District", color="Risk probability")
)
st.plotly_chart(fig_heatmap, use_container_width=True)


# ==================================================
# 5. TOP HIGH-RISK DISTRICT-MONTHS
# ==================================================
st.subheader("5. Top high-risk district-months")

top_n = st.slider("Number of top records to show", min_value=5, max_value=50, value=20, step=5)

top_risk = (
    filtered_alerts.sort_values("drought_risk_prob", ascending=False)
    [["district_name", "year", "month", "drought_risk_prob", "drought_alert", "drought_next_actual"]]
    .head(top_n)
    .reset_index(drop=True)
)

st.dataframe(top_risk, use_container_width=True)


# ==================================================
# 6. FILTERED RAW DATA
# ==================================================
st.subheader("6. Filtered alert table")

display_cols = [
    "district_id",
    "district_name",
    "year",
    "month",
    "drought_risk_prob",
    "drought_alert",
    "drought_next_actual"
]

st.dataframe(
    filtered_alerts[display_cols].sort_values(
        ["year", "month", "district_name"], ascending=[True, True, True]
    ),
    use_container_width=True
)


# ==================================================
# 7. DOWNLOAD BUTTON
# ==================================================
st.subheader("7. Download filtered data")

csv_data = filtered_alerts[display_cols].to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered alert table as CSV",
    data=csv_data,
    file_name="filtered_drought_alerts.csv",
    mime="text/csv"
)