import os
import time
import ee
import geemap
from dotenv import load_dotenv


# ==================================================
# CONFIG
# ==================================================
load_dotenv()

GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID")
if not GEE_PROJECT_ID:
    raise ValueError("GEE_PROJECT_ID is not set in the .env file.")

DISTRICTS_FILE = "data/processed/grand_sud_districts.geojson"

DISTRICT_FIELD = "district_name"
REGION_FIELD = "region_name"

START_DATE_STR = "2015-01-01"
END_DATE_STR = "2025-12-01"

BASELINE_START_STR = "2015-01-01"
BASELINE_END_STR = "2020-12-31"

EXPORT_DESCRIPTION = "grand_sud_monthly_features_v2"
EXPORT_FOLDER = "gee_exports"
EXPORT_FILENAME_PREFIX = "grand_sud_monthly_features_v2"
EXPORT_FORMAT = "CSV"

EXPORT_WAIT_SECONDS = 7200
EXPORT_POLL_INTERVAL = 20


# ==================================================
# EARTH ENGINE INITIALIZATION
# ==================================================
def initialize_earth_engine(project_id: str) -> None:
    try:
        ee.Initialize(project=project_id)
        print(f"Earth Engine initialized with project: {project_id}")
    except Exception:
        print("Earth Engine not initialized. Starting authentication...")
        ee.Authenticate()
        ee.Initialize(project=project_id)
        print(f"Earth Engine authenticated and initialized with project: {project_id}")


# ==================================================
# DATA LOADERS
# ==================================================
def load_districts():
    if not os.path.exists(DISTRICTS_FILE):
        raise FileNotFoundError(f"Boundary file not found: {DISTRICTS_FILE}")
    return geemap.geojson_to_ee(DISTRICTS_FILE)


def load_image_collections():
    return {
        "modis_ndvi": ee.ImageCollection("MODIS/061/MOD13Q1"),
        "chirps": ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY"),
        "modis_lst": ee.ImageCollection("MODIS/061/MOD11A2"),
        "modis_et": ee.ImageCollection("MODIS/061/MOD16A2GF"),
    }


# ==================================================
# MONTHLY IMAGE BUILDERS
# ==================================================
def get_monthly_ndvi(modis_ndvi, month_start, month_end):
    return (
        modis_ndvi
        .filterDate(month_start, month_end)
        .select("NDVI")
        .mean()
        .multiply(0.0001)
        .rename("ndvi_mean")
    )


def get_monthly_rain(chirps, month_start, month_end):
    return (
        chirps
        .filterDate(month_start, month_end)
        .select("precipitation")
        .sum()
        .rename("rainfall_total_mm")
    )


def get_monthly_lst_c(modis_lst, month_start, month_end):
    return (
        modis_lst
        .filterDate(month_start, month_end)
        .select("LST_Day_1km")
        .mean()
        .multiply(0.02)
        .subtract(273.15)
        .rename("lst_day_mean_c")
    )


def get_monthly_et(modis_et, month_start, month_end):
    return (
        modis_et
        .filterDate(month_start, month_end)
        .select("ET")
        .sum()
        .multiply(0.1)
        .rename("et_total_mm")
    )


# ==================================================
# CLIMATOLOGY BUILDERS
# ==================================================
def get_monthly_ndvi_climatology(modis_ndvi, baseline_start, baseline_end, month_number):
    month_number = ee.Number(month_number)
    return (
        modis_ndvi
        .filterDate(baseline_start, baseline_end)
        .filter(ee.Filter.calendarRange(month_number, month_number, "month"))
        .select("NDVI")
        .mean()
        .multiply(0.0001)
        .rename("ndvi_climatology")
    )


def get_monthly_rain_climatology(chirps, baseline_start, baseline_end, month_number):
    month_number = ee.Number(month_number)
    baseline_years = baseline_end.difference(baseline_start, "year").round().toInt()

    return (
        chirps
        .filterDate(baseline_start, baseline_end)
        .filter(ee.Filter.calendarRange(month_number, month_number, "month"))
        .select("precipitation")
        .sum()
        .divide(baseline_years)
        .rename("rain_climatology_mm")
    )


# ==================================================
# FEATURE CONSTRUCTION
# ==================================================
def build_monthly_feature_collection(
    grand_sud_districts,
    modis_ndvi,
    chirps,
    modis_lst,
    modis_et,
    start_date,
    end_date,
    baseline_start,
    baseline_end,
):
    def monthly_features(month_offset):
        month_offset = ee.Number(month_offset)

        month_start = start_date.advance(month_offset, "month")
        month_end = month_start.advance(1, "month")
        month_number = month_start.get("month")

        ndvi_img = get_monthly_ndvi(modis_ndvi, month_start, month_end)
        rain_img = get_monthly_rain(chirps, month_start, month_end)
        lst_img = get_monthly_lst_c(modis_lst, month_start, month_end)
        et_img = get_monthly_et(modis_et, month_start, month_end)

        ndvi_clim = get_monthly_ndvi_climatology(
            modis_ndvi, baseline_start, baseline_end, month_number
        )
        rain_clim = get_monthly_rain_climatology(
            chirps, baseline_start, baseline_end, month_number
        )

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
            scale=5000,
        )

        def add_time_props(feature):
            return (
                feature.set("date", month_start.format("YYYY-MM-dd"))
                .set("year", month_start.get("year"))
                .set("month", month_start.get("month"))
            )

        return reduced.map(add_time_props)

    n_months = end_date.difference(start_date, "month").toInt().add(1)
    months = ee.List.sequence(0, n_months.subtract(1))

    monthly_fc = ee.FeatureCollection(months.map(monthly_features)).flatten()

    return monthly_fc.select([
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
        "rainfall_anomaly_mm",
    ])


# ==================================================
# EXPORT HELPERS
# ==================================================
def start_export(export_fc):
    task = ee.batch.Export.table.toDrive(
        collection=export_fc,
        description=EXPORT_DESCRIPTION,
        folder=EXPORT_FOLDER,
        fileNamePrefix=EXPORT_FILENAME_PREFIX,
        fileFormat=EXPORT_FORMAT,
    )
    task.start()

    print("Export task started.")
    print(f"Task ID: {task.id}")
    print(f"Drive folder: {EXPORT_FOLDER}")
    print(f"Expected file: {EXPORT_FILENAME_PREFIX}.csv")
    return task


def wait_for_task(task, timeout_seconds=EXPORT_WAIT_SECONDS, poll_interval=EXPORT_POLL_INTERVAL):
    start_time = time.time()

    while True:
        status = task.status()
        state = status.get("state", "UNKNOWN")
        print(f"Current EE task state: {state}")

        if state == "COMPLETED":
            print("Earth Engine export completed successfully.")
            return

        if state in {"FAILED", "CANCELLED", "CANCEL_REQUESTED"}:
            raise RuntimeError(f"Earth Engine export failed: {status}")

        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            raise TimeoutError(
                f"Earth Engine export did not finish within {timeout_seconds} seconds."
            )

        time.sleep(poll_interval)


# ==================================================
# MAIN
# ==================================================
def main():
    initialize_earth_engine(GEE_PROJECT_ID)

    start_date = ee.Date(START_DATE_STR)
    end_date = ee.Date(END_DATE_STR)
    baseline_start = ee.Date(BASELINE_START_STR)
    baseline_end = ee.Date(BASELINE_END_STR)

    grand_sud_districts = load_districts()
    collections = load_image_collections()

    export_fc = build_monthly_feature_collection(
        grand_sud_districts=grand_sud_districts,
        modis_ndvi=collections["modis_ndvi"],
        chirps=collections["chirps"],
        modis_lst=collections["modis_lst"],
        modis_et=collections["modis_et"],
        start_date=start_date,
        end_date=end_date,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
    )

    task = start_export(export_fc)
    wait_for_task(task)

    print("Feature extraction step completed.")


if __name__ == "__main__":
    main()