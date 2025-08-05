"""Operational pipeline orchestrating data, models, and inundation."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

import numpy as np
import torch

from .data.chirps import fetch_chirps
from .data.geoglows import fetch_forecast
from .models.lstm import LSTMForecaster
from .models.trainer import Trainer
from .hydraulics.inundation import depth_to_extent


def run_pipeline(
    reach_id: int,
    bbox: Tuple[float, float, float, float],
    start: datetime,
    end: datetime,
    model_path: Path,
) -> list[dict]:
    """Example end-to-end forecast and inundation computation."""

    chirps = fetch_chirps(bbox, start, end)
    forecast = fetch_forecast(reach_id)

    x = torch.from_numpy(chirps.precip.values.astype(np.float32))
    x = x.unsqueeze(0).unsqueeze(-1)  # (1, time, 1)
    model = LSTMForecaster(n_features=1)
    if model_path.exists():
        model.load_state_dict(torch.load(model_path))
    trainer = Trainer(model)
    loader = trainer.to_loader(x, torch.zeros(x.size(1)))
    trainer.fit(loader, epochs=1)

    depth_raster = Path("depth.tif")
    np.zeros((1, 1))  # placeholder for generated raster
    return depth_to_extent(depth_raster)
