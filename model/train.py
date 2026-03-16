import numpy as np
import torch
from torch.nn import Module

from model.DataPreprocessing import DataFramePreprocessor
from model.InventoryForcaster import InventoryForcaster


def train(
    model: InventoryForcaster,
    data_frame_preproccesor: DataFramePreprocessor,
    optimizer: torch.optim.Optimizer,
    criterion: Module,
    epochs: int,
    device: torch.device,
) -> dict[str, list]:

    dataloader = data_frame_preproccesor.fetch_dataframe().prepare_dataframes().pandas_df_to_tensor()
    model.lstm.to(device)
    history = {"lstm_loss": [], "residual_loss": []}

    for epoch in range(epochs):
        model.lstm.train()
        epoch_lstm_loss = 0
        epoch_residual_loss = 0
        hidden = None

        for batch_idx, (x, targets) in enumerate(dataloader.train_tensor):
            x, targets = x.to(device), targets.to(device)

            # --- Phase 1: Train LSTM ---
            optimizer.zero_grad()
            lstm_out, hidden = model.lstm(x, hidden)

            # detach hidden to prevent backprop through entire history
            hidden = (hidden[0].detach(), hidden[1].detach())

            lstm_loss = criterion(lstm_out, targets)
            lstm_loss.backward()
            optimizer.step()
            epoch_lstm_loss += lstm_loss.item()

            # --- Phase 2: Fit XGBoost on residuals ---
            model.lstm.eval()
            with torch.no_grad():
                lstm_out, _ = model.lstm(x, hidden)
                residuals = (targets - lstm_out).cpu().numpy()
                lstm_out_np = lstm_out.cpu().numpy()

            model.xgboost.fit(lstm_out_np, residuals)

            # track residual loss
            residual_correction = model.xgboost.predict(lstm_out_np)
            residual_loss = np.mean(residuals**2)  # MSE of residuals
            epoch_residual_loss += residual_loss

        avg_lstm_loss = epoch_lstm_loss / len(dataloader)
        avg_residual_loss = epoch_residual_loss / len(dataloader)
        history["lstm_loss"].append(avg_lstm_loss)
        history["residual_loss"].append(avg_residual_loss)

        print(
            f"Epoch {epoch+1}/{epochs} | "
            f"LSTM Loss: {avg_lstm_loss:.4f} | "
            f"Residual Loss: {avg_residual_loss:.4f}"
        )

    return history
