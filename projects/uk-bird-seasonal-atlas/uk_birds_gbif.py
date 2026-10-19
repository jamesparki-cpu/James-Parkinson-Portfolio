"""
Seasonal distributions of 11 UK birds from eBird (Cornell Lab of Ornithology) via GBIF.

Downloads monthly counts on the EEA 10 km grid using GBIF's SQL download API,
corrects for recording effort, and writes a GeoPackage for mapping in QGIS.

Method
  effort         = observer-days (distinct observer + date) per 10 km square per month.
                   Used instead of checklists because GBIF's copy of eBird has no checklist ID.
  reporting rate = share of those observer-days on which the species was recorded.
  Cell-months with fewer than MIN_EFFORT observer-days are left blank (too little data).

Usage
  pip install requests pandas geopandas shapely
  python uk_birds_gbif.py
  Asks for your GBIF username and password (or set GBIF_USER / GBIF_PWD).
  Downloads are cached in output/; delete the CSVs to download fresh data.

Outputs (output/)
  species_counts.csv, effort_counts.csv   raw aggregated downloads
  uk_birds_monthly.gpkg                   layer 'seasonal' for QGIS (EPSG:27700)
  national_monthly_rate.csv               GB-wide reporting rate, species x month
  gbif_citation.txt                       download DOIs - cite these
"""
import io
import os
import re
import time
import zipfile
from getpass import getpass

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import box

API = "https://api.gbif.org/v1"
EBIRD_KEY = "4fa7b334-ce0d-4e88-aaae-2e0c138d049e"  # EOD - eBird Observation Dataset
YEARS = (2015, 2025)
GRID_M = 10000      # 10 km squares; use 20000 if maps are too sparse
MIN_EFFORT = 10     # min. observer-days in a cell-month before a rate is shown
OUT_DIR = "output"

SPECIES = {
    "Apus apus": "Swift",
    "Hirundo rustica": "Swallow",
    "Delichon urbicum": "House Martin",
    "Cuculus canorus": "Cuckoo",
    "Phylloscopus trochilus": "Willow Warbler",
    "Turdus iliacus": "Redwing",
    "Turdus pilaris": "Fieldfare",
    "Anser brachyrhynchus": "Pink-footed Goose",
    "Cygnus cygnus": "Whooper Swan",
    "Oenanthe oenanthe": "Wheatear",
    "Erithacus rubecula": "Robin (resident control)",
}

# ---------------------------------------------------------------- SQL
# Notes from testing GBIF's SQL API:
#  - no BETWEEN (use >= / <=), no CAST(... AS STRING) (use PRINTF)
#  - classKey = 212 matches nothing; not needed as the eBird dataset is birds only
#  - recordedBy is ARRAY<STRING>, so it is flattened with CONCAT_WS
WHERE = f"""
  datasetKey = '{EBIRD_KEY}'
  AND countryCode = 'GB'
  AND occurrenceStatus = 'PRESENT'
  AND hasCoordinate = TRUE
  AND recordedBy IS NOT NULL
  AND "day" IS NOT NULL
  AND "month" IS NOT NULL
  AND "year" >= {YEARS[0]} AND "year" <= {YEARS[1]}
  AND (coordinateUncertaintyInMeters <= 5000 OR coordinateUncertaintyInMeters IS NULL)
  AND NOT ARRAY_CONTAINS(issue, 'ZERO_COORDINATE')
  AND NOT ARRAY_CONTAINS(issue, 'COUNTRY_COORDINATE_MISMATCH')
"""
CELL = (f"GBIF_EEARGCode({GRID_M}, decimalLatitude, decimalLongitude, "
        f"COALESCE(coordinateUncertaintyInMeters, 1000))")
VISIT = ("COUNT(DISTINCT CONCAT_WS('|', CONCAT_WS(',', recordedBy), "
         "PRINTF('%04d-%02d', \"year\", \"day\")))")

NAMES = ", ".join(f"'{s}'" for s in SPECIES)
SQL_SPECIES = f"""SELECT species, "month", {CELL} AS cell, {VISIT} AS n
FROM occurrence WHERE {WHERE} AND species IN ({NAMES})
GROUP BY species, "month", {CELL}"""
SQL_EFFORT = f"""SELECT "month", {CELL} AS cell, {VISIT} AS effort
FROM occurrence WHERE {WHERE}
GROUP BY "month", {CELL}"""


# ---------------------------------------------------------------- GBIF download
def credentials():
    user = os.environ.get("GBIF_USER") or input("GBIF username (not email): ").strip()
    pwd = os.environ.get("GBIF_PWD") or getpass("GBIF password: ")
    return user, pwd


def gbif_sql(sql, label, auth):
    """Submit an SQL download, wait for it, return (DataFrame, DOI)."""
    r = requests.post(f"{API}/occurrence/download/request", auth=auth,
                      json={"sendNotification": False, "format": "SQL_TSV_ZIP",
                            "sql": " ".join(sql.split())})
    if r.status_code >= 400:
        raise SystemExit(f"[{label}] GBIF rejected the query ({r.status_code}):\n{r.text}")
    key = r.text.strip()
    print(f"[{label}] download {key} submitted")

    t0 = time.time()
    while True:
        try:
            info = requests.get(f"{API}/occurrence/download/{key}", timeout=60).json()
        except (requests.RequestException, ValueError) as e:  # wifi drop, laptop waking, etc.
            print(f"[{label}]   connection problem ({type(e).__name__}), retrying in 1 min")
            time.sleep(60)
            continue
        print(f"[{label}]   {info['status']}  ({(time.time() - t0) / 60:.0f} min)")
        if info["status"] == "SUCCEEDED":
            break
        if info["status"] in ("FAILED", "KILLED", "CANCELLED"):
            raise SystemExit(f"[{label}] download {info['status']}")
        time.sleep(60)

    z = zipfile.ZipFile(io.BytesIO(requests.get(info["downloadLink"]).content))
    with z.open(z.namelist()[0]) as f:
        df = pd.read_csv(f, sep="\t")
    df.columns = df.columns.str.lower()
    return df, info.get("doi")


def load_or_download(path, sql, label, auth_holder, dois):
    if os.path.exists(path):
        print(f"[{label}] using cached {path}")
        return pd.read_csv(path)
    if not auth_holder:
        auth_holder.append(credentials())
    df, doi = gbif_sql(sql, label, auth_holder[0])
    df.to_csv(path, index=False)
    dois.append(f"{label}: https://doi.org/{doi}")
    return df


# ---------------------------------------------------------------- processing
def cell_polygon(code):
    """'10kmE355N320' -> the 10 km square in EPSG:3035 (E/N are in units of the cell size)."""
    size, e, n = map(int, re.match(r"(\d+)kmE(\d+)N(\d+)", code).groups())
    m = size * 1000
    return box(e * m, n * m, (e + 1) * m, (n + 1) * m)


def build_table(sp, ef):
    # every species x every visited cell-month, so "visited but not recorded" = 0, not missing
    full = ef.merge(pd.DataFrame({"species": list(SPECIES)}), how="cross")
    df = full.merge(sp, on=["species", "month", "cell"], how="left").fillna({"n": 0})
    df["n"] = df["n"].astype(int)
    df["month"] = df["month"].astype(int)
    df["rate"] = (df["n"] / df["effort"]).where(df["effort"] >= MIN_EFFORT)
    df["common"] = df["species"].map(SPECIES)
    df["date"] = pd.to_datetime(dict(year=2000, month=df["month"], day=1))  # Temporal Controller
    return df


def national_rates(df):
    ok = df.dropna(subset=["rate"])
    totals = ok.groupby(["common", "month"])[["n", "effort"]].sum()
    return (totals["n"] / totals["effort"]).unstack("month")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    auth, dois = [], []
    sp = load_or_download(f"{OUT_DIR}/species_counts.csv", SQL_SPECIES, "species", auth, dois)
    ef = load_or_download(f"{OUT_DIR}/effort_counts.csv", SQL_EFFORT, "effort", auth, dois)
    if dois:
        with open(f"{OUT_DIR}/gbif_citation.txt", "a") as f:
            f.write("\n".join(dois) + "\n")

    df = build_table(sp, ef)
    gdf = gpd.GeoDataFrame(df, geometry=df["cell"].map(cell_polygon), crs=3035).to_crs(27700)
    gdf.to_file(f"{OUT_DIR}/uk_birds_monthly.gpkg", layer="seasonal", driver="GPKG")

    national = national_rates(df)
    national.round(4).to_csv(f"{OUT_DIR}/national_monthly_rate.csv")

    print("\nGB-wide reporting rate by month:")
    print(national.round(2).to_string())
    print(f"\n{ef['cell'].nunique():,} squares, {int(ef['effort'].sum()):,} observer-days; "
          f"{len(gdf):,} rows written to {OUT_DIR}/uk_birds_monthly.gpkg")


if __name__ == "__main__":
    main()
