"""GeoGLOWS streamflow forecast utilities.

Functions for downloading and processing GeoGLOWS streamflow
hindcast and forecast data using the `pygeoglows` library.
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

import pandas as pd
from pygeoglows import streamflow


def fetch_hindcast(reach_id: int, start: datetime, end: datetime) -> pd.DataFrame:
    """Return historical streamflow hindcasts for a reach."""
    return streamflow.get_hindcast(reach_id, start, end)


def fetch_forecast(reach_id: int) -> pd.DataFrame:
    """Return the latest ensemble streamflow forecast for a reach."""
    return streamflow.get_forecast(reach_id)


def aggregate_ensemble(ensemble: pd.DataFrame, quantiles: Sequence[float]) -> pd.DataFrame:
    """Aggregate ensemble forecasts to selected quantiles."""
    return ensemble.quantile(quantiles, axis=1).T
