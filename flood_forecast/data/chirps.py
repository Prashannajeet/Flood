"""CHIRPS precipitation data access utilities.

This module provides functions to download and process CHIRPS
precipitation data using the ``xarray`` and ``rasterio`` packages.
"""

from __future__ import annotations

from datetime import datetime
from typing import Tuple

import xarray as xr


def fetch_chirps(
    bbox: Tuple[float, float, float, float],
    start: datetime,
    end: datetime,
) -> xr.Dataset:
    """Fetch CHIRPS rainfall for a bounding box and time range.

    Parameters
    ----------
    bbox:
        Bounding box as ``(min_lon, min_lat, max_lon, max_lat)``.
    start, end:
        Start and end of the time period.

    Returns
    -------
    xr.Dataset
        CHIRPS precipitation over the requested region and period.
    """
    url = (
        "https://chc-data-nextgen2-geo.s3.us-west-2.amazonaws.com/chirps/v2.0/global-daily.nc"
    )
    ds = xr.open_dataset(url)
    ds = ds.sel(
        longitude=slice(bbox[0], bbox[2]),
        latitude=slice(bbox[3], bbox[1]),  # latitude reversed
        time=slice(start, end),
    )
    return ds
