"""Inundation mapping helper functions."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import shapes


def depth_to_extent(depth_raster: Path, threshold: float = 0.0) -> list[dict]:
    """Convert a water depth raster to flood extent polygons."""
    with rasterio.open(depth_raster) as src:
        mask = src.read(1) > threshold
        results = [
            {"properties": {"depth": float(val)}, "geometry": geom}
            for geom, val in shapes(mask.astype(np.uint8), transform=src.transform)
            if val == 1
        ]
    return results
