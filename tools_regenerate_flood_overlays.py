from pathlib import Path
import base64
import json
import re

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject
from pyproj import Transformer
from PIL import Image

ROOT = Path(r"D:\01 Project\Development\Mohan_Kundaliya\Data\dashboard_gis_streamlit")
SOURCE_ROOT = Path(r"D:\01 Project\Development\Mohan_Kundaliya\Flood Inundation\MKP_Dam_Break\outputs\compact_flood_rasters")
OUT_DIR = ROOT / "static" / "flood_inundation"
DASHBOARD = ROOT / "dashboard.html"
MANIFEST = OUT_DIR / "flood_inundation_manifest.json"

PROJECTS = [
    ("Kundaliya", "kundaliya"),
    ("Mohanpura", "mohanpura"),
]
SCENARIO_NAMES = ["Q25", "Q50", "Q100", "PMF"]
SCENARIOS = [
    (
        project,
        slug,
        scenario,
        SOURCE_ROOT / project / scenario / f"{project.upper()}_{scenario}_DEPTH_MAX.tif",
        1.0,
    )
    for project, slug in PROJECTS
    for scenario in SCENARIO_NAMES
]

WIDTH = 1200
DISPLAY_CRS = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs"
LEAFLET_CRS = "+proj=longlat +datum=WGS84 +no_defs"
LEGEND_MAX_DEPTH_M = 10.0
FLOOD_DEPTH_PALETTE = np.array([
    [171, 210, 250],  # #ABD2FA
    [118, 146, 255],  # #7692FF
    [27, 44, 193],    # #1B2CC1
    [9, 21, 64],      # #091540
], dtype=float)

def transformed_bounds(src, dst_crs):
    transformer = Transformer.from_crs("+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs", dst_crs, always_xy=True)
    left, bottom, right, top = src.bounds
    xs = []
    ys = []
    for x in np.linspace(left, right, 13):
        for y in (bottom, top):
            xx, yy = transformer.transform(float(x), float(y))
            xs.append(xx); ys.append(yy)
    for y in np.linspace(bottom, top, 13):
        for x in (left, right):
            xx, yy = transformer.transform(float(x), float(y))
            xs.append(xx); ys.append(yy)
    return min(xs), min(ys), max(xs), max(ys)

def leaflet_bounds_from_mercator(west, south, east, north):
    transformer = Transformer.from_crs(DISPLAY_CRS, LEAFLET_CRS, always_xy=True)
    west_lon, south_lat = transformer.transform(west, south)
    east_lon, north_lat = transformer.transform(east, north)
    return [[round(south_lat, 8), round(west_lon, 8)], [round(north_lat, 8), round(east_lon, 8)]]

def colorize_depth(data, valid):
    rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
    if not np.any(valid):
        return rgba
    normalized = np.zeros_like(data, dtype=np.float32)
    normalized[valid] = np.clip(data[valid] / LEGEND_MAX_DEPTH_M, 0, 1)
    stops = FLOOD_DEPTH_PALETTE
    scaled = normalized * (len(stops) - 1)
    low = np.floor(scaled).astype(int)
    high = np.clip(low + 1, 0, len(stops) - 1)
    frac = (scaled - low)[..., None]
    rgb = stops[low] * (1 - frac) + stops[high] * frac
    rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.where(valid, 255, 0).astype(np.uint8)
    return rgba

def make_overlay(project, project_slug, scenario, tif_path, opacity):
    with rasterio.open(tif_path) as src:
        west, south, east, north = transformed_bounds(src, DISPLAY_CRS)
        height = max(1, round(WIDTH * ((north - south) / (east - west))))
        dst_transform = from_bounds(west, south, east, north, WIDTH, height)
        dest = np.full((height, WIDTH), np.nan, dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1),
            destination=dest,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=dst_transform,
            dst_crs=DISPLAY_CRS,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
        valid = np.isfinite(dest) & (dest > 0.01)
        max_depth = float(np.nanmax(np.where(valid, dest, np.nan))) if np.any(valid) else 0.0
        rgba = colorize_depth(dest, valid)
        out_name = f"{project_slug}_{scenario.lower()}_depth_max.png"
        out_path = OUT_DIR / out_name
        Image.fromarray(rgba, "RGBA").save(out_path, optimize=True)
        return {
            "project": project,
            "scenario": scenario,
            "label": f"{project} {scenario} flood inundation depth",
            "metric": "Maximum flood depth",
            "url": f"/app/static/flood_inundation/{out_name}",
            "bounds": leaflet_bounds_from_mercator(west, south, east, north),
            "opacity": opacity,
            "maxDepthM": round(max_depth, 2),
            "peakCms": None,
            "volumeMcm": None,
            "imageSize": [WIDTH, height],
            "sourceCrs": "EPSG:32643",
            "displayCrs": "EPSG:3857",
        }

def embed_manifest(manifest):
    embedded = []
    for item in manifest:
        out_item = dict(item)
        png_path = OUT_DIR / Path(item["url"]).name
        out_item["url"] = "data:image/png;base64," + base64.b64encode(png_path.read_bytes()).decode("ascii")
        embedded.append(out_item)
    html = DASHBOARD.read_text(encoding="utf-8")
    replacement = "const floodInundationLayers = " + json.dumps(embedded, separators=(",", ":")) + ";"
    html, count = re.subn(r"const floodInundationLayers = \[.*?\];", replacement, html, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Expected to replace one floodInundationLayers block, replaced {count}")
    DASHBOARD.write_text(html, encoding="utf-8")

OUT_DIR.mkdir(parents=True, exist_ok=True)
manifest = [make_overlay(*item) for item in SCENARIOS]
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
embed_manifest(manifest)
for item in manifest:
    print(item["project"], item["scenario"], item["bounds"], item["imageSize"], item["maxDepthM"], item["sourceCrs"], "->", item["displayCrs"])
