"""Recurrent neural network model for streamflow prediction."""

from __future__ import annotations

import torch
from torch import nn


class LSTMForecaster(nn.Module):
    """Simple LSTM network for sequence-to-one forecasting."""

    def __init__(self, n_features: int, hidden_size: int = 64, n_layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_size,
            num_layers=n_layers,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        return self.fc(out)
