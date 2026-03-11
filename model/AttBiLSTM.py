import torch.nn as nn
from torch import Tensor


class AttBiLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layer, output_size):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layer, batch_first=False, bidirectional=True
        )
        self.dense_layer = nn.Linear(hidden_size * 2, output_size)
        self.attention = Attention(hidden_size=hidden_size)

    def forward(self, x, hidden=None):
        x, hidden = self.lstm(x, hidden)
        context = self.attention.compute_score(x)
        out = self.dense_layer(context)
        return out, hidden


class Attention(nn.Module):
    def __init__(self, hidden_size) -> None:
        super().__init__()
        self.softmax = nn.Softmax(dim=0)
        self.linear = nn.Linear(hidden_size, hidden_size)

    def compute_score(self, x: Tensor):
        scores = self.linear(x)
        weights = self.softmax(scores)
        context = (weights * x).sum(dim=0)
        return context
