"""Prepare web tiles from the R04 drone survey; original survey rasters stay intact."""
import argparse
import json
import math
import os
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--work', type=Path, required=True)
parser.add_argument('--gis-deps', type=Path)
args = parser.parse_args()
if args.gis_deps:
    sys.path.insert(0, str(args.gis_deps))

import geopandas as gpd
import numpy as np
from PIL import Image
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.vrt import WarpedVRT
from rasterio.warp import reproject, transform_bounds
from rasterio.windows import Window
from scipy.ndimage import distance_transform_edt

os.environ['PROJ_DATA'] = str(Path(rasterio.__file__).parent / 'proj_data')
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'static/drone_terrain'
OUT.mkdir(parents=True, exist_ok=True)
args.work.mkdir(parents=True, exist_ok=True)
ORIGIN = 20037508.342789244
TILE_SIZE = 256
MIN_ZOOM, MAX_ZOOM = 11, 16
PALETTE = np.array([[224, 244, 238], [129, 190, 166], [234, 214, 126],
                    [189, 139, 104], [111, 103, 113]], dtype=float)
SOURCES = {
    'dem': args.source / 'Mohanpura_Merged_DEM_Flights01_27_0p50m.tif',
    'ortho': args.source / 'Mohanpura_Merged_Orthomosaic_0p2053m.tif',
}


def prepare_raster(name, path):
    dest = args.work / f'{name}_web_2m.tif'
    with rasterio.open(path) as src:
        if src.crs.to_epsg() != 32643:
            raise ValueError(f'Unexpected source CRS for {path}: {src.crs}')
        bounds = transform_bounds(src.crs, 'EPSG:3857', *src.bounds, densify_pts=41)
        size = 2 * ORIGIN / (2 ** MAX_ZOOM * TILE_SIZE)
        width = math.ceil((bounds[2] - bounds[0]) / size)
        height = math.ceil((bounds[3] - bounds[1]) / size)
        transform = from_bounds(*bounds, width, height)
        if not dest.exists():
            profile = dict(driver='GTiff', width=width, height=height, count=src.count,
                           dtype=src.dtypes[0], crs='EPSG:3857', transform=transform,
                           nodata=src.nodata, tiled=True, compress='deflate', BIGTIFF='IF_SAFER')
            with rasterio.open(dest, 'w', **profile) as dst:
                for band in range(1, src.count + 1):
                    reproject(rasterio.band(src, band), rasterio.band(dst, band),
                              src_nodata=src.nodata, dst_nodata=src.nodata,
                              resampling=Resampling.average, num_threads=4, warp_mem_limit=256)
                    print(f'Prepared {name} band {band}/{src.count}', flush=True)
                if name == 'ortho':
                    dst.colorinterp = src.colorinterp
                dst.build_overviews([2, 4, 8, 16, 32], Resampling.average)
        return dest, {'file': path.name, 'sourceCrs': src.crs.to_string(),
                      'sourceResolutionM': list(src.res), 'sourceBytes': path.stat().st_size,
                      'bounds': transform_bounds(src.crs, 'EPSG:4326', *src.bounds, densify_pts=41)}


def colorize(elevation, valid, limits):
    ratio = np.clip((np.where(valid, elevation, limits[0]) - limits[0]) / (limits[1] - limits[0]), 0, 1)
    stops = ratio * (len(PALETTE) - 1)
    low = np.floor(stops).astype(int)
    high = np.minimum(low + 1, len(PALETTE) - 1)
    rgb = PALETTE[low] * (1 - (stops - low)[..., None]) + PALETTE[high] * (stops - low)[..., None]
    return np.dstack([rgb.astype('uint8'), valid.astype('uint8') * 255])


def save_tile(kind, zoom, x, y, rgba):
    path = OUT / kind / str(zoom) / str(x) / f'{y}.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba).save(path, optimize=True)


with rasterio.Env(GDAL_CACHEMAX=256 * 1024 * 1024):
    prepared = {name: prepare_raster(name, path) for name, path in SOURCES.items()}
    with rasterio.open(prepared['dem'][0]) as dem:
        sample = dem.read(1, out_shape=(1200, 800), masked=True, resampling=Resampling.nearest)
        values = sample.compressed()
        limits = [float(math.floor(values.min() / 10) * 10), float(math.ceil(values.max() / 10) * 10)]
    available = {'dem': [], 'hillshade': [], 'ortho': []}
    for name, (path, info) in prepared.items():
        with rasterio.open(path) as src:
            for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
                span = 2 * ORIGIN / 2 ** zoom
                xmin = math.floor((src.bounds.left + ORIGIN) / span)
                xmax = math.floor((src.bounds.right + ORIGIN) / span)
                ymin = math.floor((ORIGIN - src.bounds.top) / span)
                ymax = math.floor((ORIGIN - src.bounds.bottom) / span)
                res = span / TILE_SIZE
                transform = from_bounds(-ORIGIN, -ORIGIN, ORIGIN, ORIGIN,
                                        TILE_SIZE * 2 ** zoom, TILE_SIZE * 2 ** zoom)
                with WarpedVRT(src, crs='EPSG:3857', transform=transform,
                               width=TILE_SIZE * 2 ** zoom, height=TILE_SIZE * 2 ** zoom,
                               resampling=Resampling.bilinear) as vrt:
                    for x in range(xmin, xmax + 1):
                        for y in range(ymin, ymax + 1):
                            halo = 1 if name == 'dem' else 0
                            window = Window(x * TILE_SIZE - halo, y * TILE_SIZE - halo,
                                            TILE_SIZE + 2 * halo, TILE_SIZE + 2 * halo)
                            data = vrt.read(window=window, masked=True)
                            key = f'{zoom}/{x}/{y}'
                            if name == 'dem':
                                valid = ~np.ma.getmaskarray(data[0]) & np.isfinite(data[0].data)
                                core = valid[1:-1, 1:-1]
                                if not core.any():
                                    continue
                                elevation = data[0].data
                                save_tile('dem', zoom, x, y, colorize(elevation[1:-1, 1:-1], core, limits))
                                available['dem'].append(key)
                                # Fill nodata only for slope calculation; the original validity mask is retained.
                                if not valid.all():
                                    indices = distance_transform_edt(~valid, return_distances=False, return_indices=True)
                                    elevation = elevation[tuple(indices)]
                                latitude = math.degrees(math.atan(math.sinh((ORIGIN - (y + .5) * span) / 6378137)))
                                gy, gx = np.gradient(elevation, res * math.cos(math.radians(latitude)))
                                azimuth = math.radians(315)
                                altitude = math.radians(45)
                                shade = (np.sin(altitude) + np.cos(altitude) *
                                         (-gx * np.sin(azimuth) + gy * np.cos(azimuth))) / np.sqrt(1 + gx * gx + gy * gy)
                                grey = np.clip(255 * (.18 + .82 * np.clip(shade, 0, 1)), 0, 255).astype('uint8')[1:-1, 1:-1]
                                save_tile('hillshade', zoom, x, y, np.dstack([grey, grey, grey, core.astype('uint8') * 255]))
                                available['hillshade'].append(key)
                            else:
                                if data.shape[0] != 4:
                                    raise ValueError('Expected RGB + alpha orthomosaic')
                                rgba = np.moveaxis(data.filled(0), 0, -1).astype('uint8')
                                if not rgba[..., 3].any():
                                    continue
                                save_tile('ortho', zoom, x, y, rgba)
                                available['ortho'].append(key)
                print(f'{name} zoom {zoom}: {len(available[name])} cumulative tiles', flush=True)

    aoi = gpd.read_file(args.source / 'Review/Processed_Coverage.gpkg', layer='final_aoi_reference').to_crs(4326)
    aoi_json = json.loads(aoi[['geometry']].to_json())
    bounds = aoi.total_bounds.tolist()
    coverage = json.loads((args.source / 'AOI_Coverage_Check.json').read_text())
    manifest = {
        'revision': 'R04', 'survey': 'Mohanpura flights 01-27', 'sourceDate': '2026-10-08',
        'sourceCrs': 'EPSG:32643', 'displayCrs': 'EPSG:3857',
        'minZoom': MIN_ZOOM, 'maxNativeZoom': MAX_ZOOM,
        'tileResolutionMAtMaxZoom': 2 * ORIGIN / (2 ** MAX_ZOOM * TILE_SIZE),
        'elevationRangeM': limits, 'palette': ['#e0f4ee', '#81bea6', '#ead67e', '#bd8b68', '#6f6771'],
        'aoi': aoi_json, 'aoiBounds': [[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
        'sources': {name: info for name, (_, info) in prepared.items()},
        'availableTiles': available, 'coverage': coverage,
        'hillshade': {'azimuthDeg': 315, 'altitudeDeg': 45, 'verticalExaggeration': 1},
        'elevationReference': 'Part 01 project reference; external vertical datum unverified',
        'limitations': 'R04 working revision. Far-field elevation accuracy and local ortho alignment remain under review. Missing coverage is transparent.',
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, separators=(',', ':')), encoding='utf-8')
    print(json.dumps({'tiles': {k: len(v) for k, v in available.items()}, 'elevationRangeM': limits}), flush=True)
