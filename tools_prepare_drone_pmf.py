"""Publish PMF depth tiles and source-cell depth/WSE samples without changing the model."""
import argparse
import json
import math
import os
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--gis-deps', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.gis_deps))
import numpy as np
import rasterio
from PIL import Image
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window

os.environ['PROJ_DATA'] = str(Path(rasterio.__file__).parent / 'proj_data')
OUT = Path(__file__).resolve().parent / 'static/drone_pmf'
OUT.mkdir(parents=True, exist_ok=True)
ORIGIN = 20037508.342789244
PALETTE = np.array([[171,210,250],[118,146,255],[27,44,193],[9,21,64]])

with rasterio.open(args.source / 'MOHANPURA_PMF_DEPTH_MAX.tif') as depth, rasterio.open(args.source / 'MOHANPURA_PMF_WSE_MAX.tif') as wse:
    assert depth.crs.to_epsg() == 32643
    assert (depth.crs, depth.shape, depth.transform) == (wse.crs, wse.shape, wse.transform)
    d = depth.read(1, masked=True)
    w = wse.read(1, masked=True)
    wet = ~np.ma.getmaskarray(d) & np.isfinite(d.data) & (d.data > .01)
    rows, cols = np.where(wet)
    samples = []
    # Sparse source-grid blocks retain individual 30 m cells; no web-image sampling.
    for block in np.unique((rows // 256) * math.ceil(depth.width / 256) + cols // 256):
        by, bx = divmod(int(block), math.ceil(depth.width / 256))
        r0, c0 = by * 256, bx * 256
        rr, cc = np.where(wet[r0:r0+256, c0:c0+256])
        records = [[int(r*256+c), float(d.data[r0+r,c0+c]),
                    None if np.ma.getmaskarray(w)[r0+r,c0+c] or not np.isfinite(w.data[r0+r,c0+c]) else float(w.data[r0+r,c0+c])]
                   for r,c in zip(rr,cc)]
        path = OUT / 'samples' / str(by) / f'{bx}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(records, separators=(',',':'), allow_nan=False))
        samples.append(f'{by}/{bx}')
    xs = depth.transform.c + (cols+.5)*depth.transform.a
    ys = depth.transform.f + (rows+.5)*depth.transform.e
    mx, my = Transformer.from_crs(depth.crs, 3857, always_xy=True).transform(xs,ys)
    available = []
    for z in range(10,15):
        span = 2*ORIGIN / 2**z
        tx, ty = np.floor((mx+ORIGIN)/span).astype(int), np.floor((ORIGIN-my)/span).astype(int)
        candidates = set(zip(tx.tolist(),ty.tolist()))
        candidates = {(x+dx,y+dy) for x,y in candidates for dx in [-1,0,1] for dy in [-1,0,1]}
        transform = from_bounds(-ORIGIN,-ORIGIN,ORIGIN,ORIGIN,256*2**z,256*2**z)
        with WarpedVRT(depth, crs='EPSG:3857', transform=transform, width=256*2**z, height=256*2**z, resampling=Resampling.nearest) as vrt:
            for x,y in sorted(candidates):
                data = vrt.read(1, window=Window(x*256,y*256,256,256), masked=True)
                valid = ~np.ma.getmaskarray(data) & np.isfinite(data.data) & (data.data>.01)
                if not valid.any():
                    continue
                stops = np.clip(np.where(valid,data.data,0)/10,0,1)*3
                low = np.floor(stops).astype(int)
                frac = (stops-low)[...,None]
                rgb = PALETTE[low]*(1-frac)+PALETTE[np.minimum(low+1,3)]*frac
                rgba = np.dstack([rgb.astype('uint8'),valid.astype('uint8')*255])
                path = OUT / 'depth' / str(z) / str(x) / f'{y}.png'
                path.parent.mkdir(parents=True,exist_ok=True)
                Image.fromarray(rgba).save(path,optimize=True)
                available.append(f'{z}/{x}/{y}')
        print(f'Zoom {z}: {len(available)} cumulative tiles',flush=True)
    manifest = {
        'scenario':json.loads((args.source/'scenario_metadata.json').read_text()),
        'minZoom':10,'maxNativeZoom':14,'availableTiles':available,'sampleBlocks':samples,
        'grid':{'width':depth.width,'height':depth.height,'left':depth.transform.c,'top':depth.transform.f,'resolutionM':30,'blockSize':256},
        'palette':['#ABD2FA','#7692FF','#1B2CC1','#091540'],'legendMaxDepthM':10,
        'wetThresholdM':.01,'wetCellCount':int(wet.sum()),'maxDepthM':float(d.data[wet].max()),
        'verticalReference':'Model elevation reference; external vertical datum unverified. Not reconciled with drone DEM.',
        'sampling':'Native 30 m source cell. Depth and WSE are independent scenario maxima, not necessarily simultaneous.'
    }
    (OUT/'manifest.json').write_text(json.dumps(manifest,separators=(',',':')))
    print(f'Published {len(available)} tiles, {len(samples)} blocks, {wet.sum()} wet cells',flush=True)
