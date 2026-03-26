import numpy as np
import torch
from sklearn.metrics import mean_absolute_error


def evaluate(model, dataloader, criterion, device, target_scaler):
    model.lstm.eval()
    total_loss = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for x, targets in dataloader:
            x, targets = x.to(device), targets.to(device)
            lstm_out, _ = model.lstm(x)
            lstm_out_np = lstm_out.cpu().numpy()
            residual_correction = model.xgboost.predict(lstm_out_np)
            combined_pred = lstm_out + torch.tensor(
                residual_correction, dtype=torch.float32
            ).unsqueeze(1).to(device)
            loss = criterion(combined_pred, targets)
            total_loss += loss.item()
            all_preds.append(combined_pred.cpu().numpy())
            all_targets.append(targets.cpu().numpy())

    avg_normalised_mae = total_loss / len(dataloader)

    all_preds_real = target_scaler.inverse_transform(np.vstack(all_preds))
    all_targets_real = target_scaler.inverse_transform(np.vstack(all_targets))

    # Directly comparable to SARIMA's MAE
    mae_real = mean_absolute_error(all_targets_real, all_preds_real)

    return avg_normalised_mae, mae_real
