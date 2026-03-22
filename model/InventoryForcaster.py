from dataclasses import dataclass

import torch
from torch.nn import Module
from xgboost import XGBRegressor

from model.AttBiLSTM import AttBiLSTM


@dataclass
class AttBiLSTMParams:
    input_size: int
    hidden_size: int
    num_layer: int
    output_layer: int


@dataclass
class XGBoostParams:
    n_estimator: int = 100
    max_depth: int = 6
    learning_rate: float = 0.1


class InventoryForcaster(Module):
    def __init__(self, lstm_params: AttBiLSTMParams, xGradient_params: XGBoostParams):
        super().__init__()
        self.lstm = AttBiLSTM(
            lstm_params.input_size,
            lstm_params.hidden_size,
            lstm_params.num_layer,
            lstm_params.output_layer,
        )
        self.xgboost = XGBRegressor(
            n_estimators=xGradient_params.n_estimator,
            max_depth=xGradient_params.max_depth,
            learning_rate=xGradient_params.learning_rate,
        )

    def forward(self, x, targets, hidden):
        lstm_out, hidden = self.lstm(x, hidden)
        residual = targets - lstm_out.detach()

        lstm_out_np = lstm_out.numpy()
        residual_np = residual.numpy()

        self.xgboost.fit(lstm_out_np, residual_np)
        residual_correction = self.xgboost.predict(lstm_out_np)

        out = lstm_out + torch.tensor(residual_correction)

        return out, residual, hidden
