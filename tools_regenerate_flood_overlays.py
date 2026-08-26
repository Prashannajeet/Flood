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
SOURCE_ROOT = Path(r"D:\01 Project\Development\Mohan_Kundaliya\Flood Inundation\MKP_Dam_Break\outputs\compact_flood_rasters\Kundaliya")
OUT_DIR = ROOT / "static" / "flood_inundation"
DASHBOARD = ROOT / "dashboard.html"
MANIFEST = OUT_DIR / "flood_inundation_manifest.json"

SCENARIOS = [
    ("Q25", SOURCE_ROOT / "Q25" / "KUNDALIYA_Q25_DEPTH_MAX.tif", 0.68),
    ("Q50", SOURCE_ROOT / "Q50" / "KUNDALIYA_Q50_DEPTH_MAX.tif", 0.68),
    ("Q100", SOURCE_ROOT / "Q100" / "KUNDALIYA_Q100_DEPTH_MAX.tif", 0.68),
    ("PMF", SOURCE_ROOT / "PMF" / "KUNDALIYA_PMF_DEPTH_MAX.tif", 0.62),
]

WIDTH = 1200
DST_CRS = "+proj=longlat +datum=WGS84 +no_defs"

def transformed_bounds(src):
    transformer = Transformer.from_crs("+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs", DST_CRS, always_xy=True)
    left, bottom, right, top = src.bounds
    xs = []
    ys = []
    for x in np.linspace(left, right, 13):
        for y in (bottom, top):
            lon, lat = transformer.transform(float(x), float(y))
            xs.append(lon); ys.append(lat)
    for y in np.linspace(bottom, top, 13):
        for x in (left, right):
            lon, lat = transformer.transform(float(x), float(y))
            xs.append(lon); ys.append(lat)
    return min(xs), min(ys), max(xs), max(ys)

def colorize_depth(data, valid, max_depth):
    rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
    if not np.any(valid):
        return rgba
    normalized = np.zeros_like(data, dtype=np.float32)
    normalized[valid] = np.clip(data[valid] / max(max_depth, 0.001), 0, 1)
    stops = np.array([
        [214, 240, 255],
        [107, 185, 226],
        [35, 113, 186],
        [12, 48, 112],
    ], dtype=float)
    scaled = normalized * (len(stops) - 1)
    low = np.floor(scaled).astype(int)
    high = np.clip(low + 1, 0, len(stops) - 1)
    frac = (scaled - low)[..., None]
    rgb = stops[low] * (1 - frac) + stops[high] * frac
    rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    alpha = np.where(normalized > 0, 72 + normalized * 178, 0)
    rgba[..., 3] = np.where(valid, np.clip(alpha, 0, 230), 0).astype(np.uint8)
    return rgba

def make_overlay(scenario, tif_path, opacity):
    with rasterio.open(tif_path) as src:
        west, south, east, north = transformed_bounds(src)
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
            dst_crs=DST_CRS,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
        valid = np.isfinite(dest) & (dest > 0.01)
        max_depth = float(np.nanmax(np.where(valid, dest, np.nan))) if np.any(valid) else 0.0
        rgba = colorize_depth(dest, valid, max_depth)
        out_name = f"kundaliya_{scenario.lower()}_depth_max.png"
        out_path = OUT_DIR / out_name
        Image.fromarray(rgba, "RGBA").save(out_path, optimize=True)
        return {
            "scenario": scenario,
            "label": f"Kundaliya {scenario} flood inundation depth",
            "metric": "Maximum flood depth",
            "url": f"/app/static/flood_inundation/{out_name}",
            "bounds": [[round(south, 8), round(west, 8)], [round(north, 8), round(east, 8)]],
            "opacity": opacity,
            "maxDepthM": round(max_depth, 2),
            "peakCms": None,
            "volumeMcm": None,
            "imageSize": [WIDTH, height],
            "sourceCrs": "EPSG:32643",
            "displayCrs": "EPSG:4326",
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
    print(item["scenario"], item["bounds"], item["imageSize"], item["maxDepthM"], item["sourceCrs"], "->", item["displayCrs"])
