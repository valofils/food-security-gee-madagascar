import os
import ee
import geemap
from dotenv import load_dotenv

# --------------------------------------------------
# 1. Load environment variables
# --------------------------------------------------
load_dotenv()

GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID")
if not GEE_PROJECT_ID:
    raise ValueError("GEE_PROJECT_ID is not set in the .env file.")

DISTRICTS_FILE = "data/processed/grand_sud_districts.geojson"

DISTRICT_FIELD = "district_name"
REGION_FIELD = "region_name"


# --------------------------------------------------
# 2. Initialize Earth Engine
# --------------------------------------------------
def initialize_earth_engine(project_id: str) -> None:
    try:
        ee.Initialize(project=project_id)
        print(f"Earth Engine initialized with project: {project_id}")
    except Exception:
        print("Earth Engine not initialized. Starting authentication...")
        ee.Authenticate()
        ee.Initialize(project=project_id)
        print(f"Earth Engine authenticated and initialized with project: {project_id}")


initialize_earth_engine(GEE_PROJECT_ID)

# --------------------------------------------------
# 3. Define dates AFTER initialization
# --------------------------------------------------
START_DATE = ee.Date("2015-01-01")
END_DATE = ee.Date("2025-12-01")

BASELINE_START = ee.Date("2015-01-01")
BASELINE_END = ee.Date("2020-12-31")


# --------------------------------------------------
# 4. Load Grand Sud boundaries
# --------------------------------------------------
if not os.path.exists(DISTRICTS_FILE):
    raise FileNotFoundError(f"Boundary file not found: {DISTRICTS_FILE}")

grand_sud_districts = geemap.geojson_to_ee(DISTRICTS_FILE)


# --------------------------------------------------
# 4. Load image collections
# --------------------------------------------------
# MOD13Q1 NDVI: 16-day, 250m, scale factor 0.0001
modis_ndvi = ee.ImageCollection("MODIS/061/MOD13Q1")

# CHIRPS rainfall: daily precipitation in mm/day
chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")

# MOD11A2 LST: 8-day, 1km, scale factor 0.02 Kelvin
modis_lst = ee.ImageCollection("MODIS/061/MOD11A2")

# MOD16A2GF ET: 8-day, 500m, ET scale factor 0.1
modis_et = ee.ImageCollection("MODIS/061/MOD16A2GF")


# --------------------------------------------------
# 5. Monthly image builders
# --------------------------------------------------
def get_monthly_ndvi(month_start, month_end):
    return (
        modis_ndvi
        .filterDate(month_start, month_end)
        .select("NDVI")
        .mean()
        .multiply(0.0001)
        .rename("ndvi_mean")
    )


def get_monthly_rain(month_start, month_end):
    return (
        chirps
        .filterDate(month_start, month_end)
        .select("precipitation")
        .sum()
        .rename("rainfall_total_mm")
    )


def get_monthly_lst_c(month_start, month_end):
    return (
        modis_lst
        .filterDate(month_start, month_end)
        .select("LST_Day_1km")
        .mean()
        .multiply(0.02)
        .subtract(273.15)
        .rename("lst_day_mean_c")
    )


def get_monthly_et(month_start, month_end):
    # ET in MOD16A2GF is scaled by 0.1 and stored as total over each 8-day period.
    # Summing the monthly composites gives monthly ET.
    return (
        modis_et
        .filterDate(month_start, month_end)
        .select("ET")
        .sum()
        .multiply(0.1)
        .rename("et_total_mm")
    )


# --------------------------------------------------
# 6. Monthly climatology for anomalies
# --------------------------------------------------
def get_monthly_ndvi_climatology(month_number):
    month_number = ee.Number(month_number)
    return (
        modis_ndvi
        .filterDate(BASELINE_START, BASELINE_END)
        .filter(ee.Filter.calendarRange(month_number, month_number, "month"))
        .select("NDVI")
        .mean()
        .multiply(0.0001)
        .rename("ndvi_climatology")
    )


def get_monthly_rain_climatology(month_number):
    month_number = ee.Number(month_number)
    return (
        chirps
        .filterDate(BASELINE_START, BASELINE_END)
        .filter(ee.Filter.calendarRange(month_number, month_number, "month"))
        .select("precipitation")
        .sum()
        # Sum over all daily images for all baseline years, then divide by number of years
        .divide(6)  # 2015, 2016, 2017, 2018, 2019, 2020
        .rename("rain_climatology_mm")
    )


# --------------------------------------------------
# 7. Per-month feature construction
# --------------------------------------------------
def monthly_features(month_offset):
    month_offset = ee.Number(month_offset)

    month_start = START_DATE.advance(month_offset, "month")
    month_end = month_start.advance(1, "month")
    month_number = month_start.get("month")

    ndvi_img = get_monthly_ndvi(month_start, month_end)
    rain_img = get_monthly_rain(month_start, month_end)
    lst_img = get_monthly_lst_c(month_start, month_end)
    et_img = get_monthly_et(month_start, month_end)

    ndvi_clim = get_monthly_ndvi_climatology(month_number)
    rain_clim = get_monthly_rain_climatology(month_number)

    ndvi_anom = ndvi_img.subtract(ndvi_clim).rename("ndvi_anomaly")
    rain_anom = rain_img.subtract(rain_clim).rename("rainfall_anomaly_mm")

    combined = (
        ndvi_img
        .addBands(rain_img)
        .addBands(lst_img)
        .addBands(et_img)
        .addBands(ndvi_anom)
        .addBands(rain_anom)
    )

    reduced = combined.reduceRegions(
        collection=grand_sud_districts,
        reducer=ee.Reducer.mean(),
        scale=5000
    )

    def add_time_props(feature):
        return (
            feature.set("date", month_start.format("YYYY-MM-dd"))
                   .set("year", month_start.get("year"))
                   .set("month", month_start.get("month"))
        )

    return reduced.map(add_time_props)


# --------------------------------------------------
# 8. Build month list and full panel
# --------------------------------------------------
n_months = END_DATE.difference(START_DATE, "month").toInt().add(1)
months = ee.List.sequence(0, n_months.subtract(1))

monthly_fc = ee.FeatureCollection(months.map(monthly_features)).flatten()


# --------------------------------------------------
# 9. Select export fields
# --------------------------------------------------
export_fc = monthly_fc.select([
    "district_id",
    DISTRICT_FIELD,
    REGION_FIELD,
    "adm0_name",
    "date",
    "year",
    "month",
    "ndvi_mean",
    "rainfall_total_mm",
    "lst_day_mean_c",
    "et_total_mm",
    "ndvi_anomaly",
    "rainfall_anomaly_mm"
])


# --------------------------------------------------
# 10. Export to Google Drive
# --------------------------------------------------
task = ee.batch.Export.table.toDrive(
    collection=export_fc,
    description="grand_sud_monthly_features_v2",
    folder="gee_exports",
    fileNamePrefix="grand_sud_monthly_features_v2",
    fileFormat="CSV"
)

task.start()

print("Export task started.")
print(f"Task ID: {task.id}")
print("Expected outputs: NDVI, rainfall, LST, ET, NDVI anomaly, rainfall anomaly.")