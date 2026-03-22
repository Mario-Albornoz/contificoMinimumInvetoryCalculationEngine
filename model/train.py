import numpy as np
import torch
from torch.nn import Module
from torch.utils.data import DataLoader, TensorDataset

from model.InventoryForcaster import InventoryForcaster


def train(
    model: InventoryForcaster,
    dataloader: DataLoader[TensorDataset],
    optimizer: torch.optim.Optimizer,
    criterion: Module,
    epochs: int,
    device: torch.device,
) -> dict[str, list]:

    model.lstm.to(device)
    history = {"lstm_loss": [], "residual_loss": [], "combined_loss": []}
    best_loss = float("inf")

    for epoch in range(epochs):
        print(f"starting epoch #{epoch + 1}")
        model.lstm.train()
        epoch_lstm_loss = 0
        epoch_residual_loss = 0
        epoch_combined_loss = 0

        for batch_idx, (x, targets) in enumerate(dataloader):  # type: ignore

            hidden = None
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

            combined_pred = lstm_out + torch.tensor(
                residual_correction, dtype=torch.float32
            ).unsqueeze(dim=1).to(device)
            combined_loss = criterion(combined_pred, targets).item()
            epoch_combined_loss += combined_loss

        avg_lstm_loss = epoch_lstm_loss / len(dataloader)
        avg_residual_loss = epoch_residual_loss / len(dataloader)
        avg_combined_loss = epoch_combined_loss / len(dataloader)
        history["lstm_loss"].append(avg_lstm_loss)
        history["residual_loss"].append(avg_residual_loss)
        history["combined_loss"].append(avg_combined_loss)

        if avg_combined_loss < best_loss:
            best_loss = avg_combined_loss
            torch.save(model.lstm.state_dict(), "best_model.pt")
            model.xgboost.save_model("best_model_xgboost.json")
            print(f"  ✓ saved best model (combined loss: {best_loss:.4f})")

        print(
            f"Epoch {epoch+1}/{epochs} | "
            f"LSTM Loss: {avg_lstm_loss:.4f} | "
            f"Residual Loss: {avg_residual_loss:.4f} |"
            f"Combined Loss: {avg_combined_loss:.4f} "
        )

    return history
