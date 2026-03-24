import torch


def evaluate(model, dataloader, criterion, device, target_scaler):
    model.lstm.eval()
    total_loss = 0

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

    avg_loss = total_loss / len(dataloader)
    real_unit_error = avg_loss * target_scaler.scale_[0]
    return avg_loss, real_unit_error
