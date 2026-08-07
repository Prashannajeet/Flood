"""Training utilities for hydrologic models."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import torch
from torch import nn, optim
from torch.utils.data import DataLoader, TensorDataset

from .lstm import LSTMForecaster


class Trainer:
    """Basic PyTorch training loop wrapper."""

    def __init__(self, model: nn.Module, lr: float = 1e-3):
        self.model = model
        self.optim = optim.Adam(model.parameters(), lr=lr)
        self.loss_fn = nn.MSELoss()

    def fit(self, loader: DataLoader, epochs: int = 10) -> None:
        self.model.train()
        for _ in range(epochs):
            for x, y in loader:
                self.optim.zero_grad()
                pred = self.model(x)
                loss = self.loss_fn(pred.squeeze(), y)
                loss.backward()
                self.optim.step()

    @staticmethod
    def to_loader(x: torch.Tensor, y: torch.Tensor, batch_size: int = 32) -> DataLoader:
        ds = TensorDataset(x, y)
        return DataLoader(ds, batch_size=batch_size, shuffle=True)

    def save(self, path: Path) -> None:
        torch.save(self.model.state_dict(), path)


__all__ = ["LSTMForecaster", "Trainer"]
