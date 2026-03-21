from pathlib import Path
import geopandas as gpd

RAW_PATH = Path("data/raw/mdg_adm2_geoboundaries.geojson")
OUT_ALL = Path("data/processed/madagascar_districts_clean.geojson")
OUT_GRAND_SUD = Path("data/processed/grand_sud_districts.geojson")

DISTRICT_TO_REGION = {
    # Androy
    "Ambovombe-Androy": "Androy",
    "Bekily": "Androy",
    "Beloha": "Androy",
    "Tsihombe": "Androy",

    # Anosy
    "Amboasary Atsimo": "Anosy",
    "Amboasary-Atsimo": "Anosy",
    "Betroka": "Anosy",
    "Taolagnaro": "Anosy",

    # Atsimo-Andrefana
    "Ampanihy": "Atsimo-Andrefana",
    "Ampanihy Ouest": "Atsimo-Andrefana",
    "Ankazoabo": "Atsimo-Andrefana",
    "Benenitra": "Atsimo-Andrefana",
    "Betioky Atsimo": "Atsimo-Andrefana",
    "Beroroha": "Atsimo-Andrefana",
    "Morombe": "Atsimo-Andrefana",
    "Sakaraha": "Atsimo-Andrefana",
    "Toliara-I": "Atsimo-Andrefana",
    "Toliara-II": "Atsimo-Andrefana",
    "Toliara I": "Atsimo-Andrefana",
    "Toliara II": "Atsimo-Andrefana",
    "Tuléar I": "Atsimo-Andrefana",
    "Tuléar II": "Atsimo-Andrefana",
}

def normalize_text(x):
    if x is None:
        return None
    return str(x).strip()

def slugify(x):
    if x is None:
        return "na"
    return (
        str(x).strip().lower()
        .replace("'", "")
        .replace(" ", "_")
        .replace("-", "_")
    )

def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {RAW_PATH}")

    gdf = gpd.read_file(RAW_PATH)

    print("Columns found:")
    print(list(gdf.columns))
    print(f"Rows: {len(gdf)}")

    gdf["district_name"] = gdf["shapeName"].map(normalize_text)
    gdf["adm0_name"] = "Madagascar"
    gdf["source"] = "geoBoundaries ADM2 via HDX"

    # Manual mapping from district to region
    gdf["region_name"] = gdf["district_name"].map(DISTRICT_TO_REGION)

    gdf["district_id"] = gdf["district_name"].map(slugify)

    keep_cols = [
        "district_id",
        "district_name",
        "region_name",
        "adm0_name",
        "source",
        "geometry",
    ]
    gdf = gdf[keep_cols].copy()

    OUT_ALL.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUT_ALL, driver="GeoJSON")

    grand_sud = gdf[gdf["region_name"].notna()].copy()
    grand_sud.to_file(OUT_GRAND_SUD, driver="GeoJSON")

    print(f"Saved full cleaned file: {OUT_ALL}")
    print(f"Saved Grand Sud subset: {OUT_GRAND_SUD}")
    print(f"Grand Sud districts: {len(grand_sud)}")

    print("\nGrand Sud districts found:")
    print(sorted(grand_sud["district_name"].tolist()))

    print("\nExample unmapped districts:")
    unmapped = sorted(gdf[gdf["region_name"].isna()]["district_name"].tolist())
    print(unmapped[:20])

if __name__ == "__main__":
    main()