"""
Turns the 10 km reporting-rate squares into smooth surfaces (GeoTIFFs) for the QGIS atlas.

Method (effort-weighted kernel smoothing)
  Each 10 km square's species count (n) and effort (observer-days) are placed at the square's
  centre on a 2 km grid, then BOTH are smoothed with the same Gaussian kernel. The smoothed
  rate is smoothed(n) / smoothed(effort), so busy squares count for more than quiet ones and
  a single lucky record in a quiet square can't paint a whole region.
  Pixels are left blank (NoData) where kernel-weighted effort < MIN_EFFORT, or off the land.

Usage
  pip install geopandas rasterio scipy
  python smooth_surfaces.py
  Reads  output/uk_birds_monthly.gpkg (+ ne_10m_admin_0_countries.shp if present)
  Writes output/surfaces/<Species>.tif - one file per species, band 1-12 = Jan-Dec, EPSG:27700
"""
import os

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
from scipy.ndimage import gaussian_filter

GPKG = "output/uk_birds_monthly.gpkg"
COAST = "ne_10m_admin_0_countries.shp"   # optional; falls back to the data footprint
OUT = "output/surfaces"

PIXEL = 2000                      # 2 km pixels
SIGMA_M = 8000                    # smoothing bandwidth (Gaussian sigma) - bigger = smoother
MIN_EFFORT = 10                   # kernel-weighted observer-days needed to show a value
X0, Y0, X1, Y1 = -20000, 0, 680000, 1230000   # BNG extent: N. Ireland to Shetland
NODATA = -9999.0


def grid_shape():
    return int((Y1 - Y0) / PIXEL), int((X1 - X0) / PIXEL)


TRANSFORM = from_origin(X0, Y1, PIXEL, PIXEL)


def land_mask(squares):
    rows, cols = grid_shape()
    if os.path.exists(COAST):
        land = gpd.read_file(COAST)
        land = land[land["ADMIN"] == "United Kingdom"].to_crs(27700)
        print("Land mask: Natural Earth coastline")
    else:
        land = squares[squares["effort"] > 0].dissolve()
        print("Land mask: data footprint (no coastline file found)")
    return rasterize(((g, 1) for g in land.geometry), out_shape=(rows, cols),
                     transform=TRANSFORM, fill=0, dtype="uint8").astype(bool)


def to_pixels(x, y):
    rows, cols = grid_shape()
    c = ((x - X0) // PIXEL).astype(int)
    r = ((Y1 - y) // PIXEL).astype(int)
    ok = (r >= 0) & (r < rows) & (c >= 0) & (c < cols)
    return r[ok], c[ok], ok


def smooth_month(df_month, land):
    """df_month: one species, one month, columns n, effort, x, y (square centres)."""
    rows, cols = grid_shape()
    n_grid = np.zeros((rows, cols))
    e_grid = np.zeros((rows, cols))
    r, c, ok = to_pixels(df_month["x"].to_numpy(), df_month["y"].to_numpy())
    np.add.at(n_grid, (r, c), df_month["n"].to_numpy()[ok])
    np.add.at(e_grid, (r, c), df_month["effort"].to_numpy()[ok])

    sigma = SIGMA_M / PIXEL
    n_s = gaussian_filter(n_grid, sigma, mode="constant")
    e_s = gaussian_filter(e_grid, sigma, mode="constant")
    weighted_effort = e_s * 2 * np.pi * sigma ** 2   # weight 1 at distance 0

    rate = np.full((rows, cols), NODATA, dtype="float32")
    good = land & (weighted_effort >= MIN_EFFORT)
    rate[good] = (n_s[good] / e_s[good]).astype("float32")
    return rate


def main():
    os.makedirs(OUT, exist_ok=True)
    gdf = gpd.read_file(GPKG, layer="seasonal")
    centres = gdf.geometry.centroid
    gdf["x"], gdf["y"] = centres.x, centres.y
    squares = gdf.drop_duplicates("cell")
    land = land_mask(squares)
    rows, cols = grid_shape()

    for common, df in gdf.groupby("common"):
        name = common.split(" (")[0].replace(" ", "_")
        path = os.path.join(OUT, f"{name}.tif")
        with rasterio.open(path, "w", driver="GTiff", height=rows, width=cols, count=12,
                           dtype="float32", crs="EPSG:27700", transform=TRANSFORM,
                           nodata=NODATA, compress="deflate") as dst:
            for m in range(1, 13):
                dst.write(smooth_month(df[df["month"] == m], land), m)
                dst.set_band_description(m, f"month {m:02d}")
        print("wrote", path)


if __name__ == "__main__":
    main()
