# Minimum Inventory Prediction Engine

This project implements a hybrid ensemble model for predicting minimum inventory levels across product and warehouse combinations. The model combines an Attention Bidirectional LSTM for learning temporal demand patterns with an XGBoost regressor that corrects the LSTM's systematic errors on structured features. A SARIMA benchmark is included for evaluation comparison.

---

WARNING: This project requires Python 3.11 specifically. Using any other Python version may cause dependency conflicts or unexpected runtime errors, particularly with PyTorch and the statsmodels SARIMAX implementation. Please verify your Python version before proceeding.

---


## Prerequisites

Before setting up the project, ensure the following are installed on your system.

Python 3.11 is required. You can download it from https://www.python.org/downloads/. To verify your version run:

    python3 --version

pip is required for installing dependencies. It is included with Python 3.11 by default. To verify run:

    pip --version

git is required to clone the repository. To verify run:

    git --version


## Project Structure

    minInvEngine/
    |-- main.py                          Entry point
    |-- requirements.txt                 Python dependencies
    |-- data/                            Raw and processed data
    |-- evaluation/
    |   |-- SARIMAbenchmark.py           SARIMA baseline benchmark
    |-- models/
    |   |-- AttBiLSTM.py                 Attention Bidirectional LSTM
    |   |-- InventoryForecaster.py       Ensemble model combining LSTM and XGBoost
    |-- training/
    |   |-- train.py                     Training loop
    |   |-- evaluate.py                  Evaluation function
    |-- preprocessing/
        |-- DataFramePreprocessor.py     Data loading and preprocessing


## Setup Instructions

Follow these steps in order.

Step 1. Clone the repository.

    git clone https://github.com/your-org/minInvEngine.git
    cd minInvEngine

Step 2. Create a virtual environment using Python 3.11. This isolates the project dependencies from your system Python.

On macOS and Linux:

    python3.11 -m venv venv
    source venv/bin/activate

On Windows:

    python3.11 -m venv venv
    venv\Scripts\activate

Once activated, your terminal prompt will show the name of the virtual environment.

Step 3. Install all dependencies.

    pip install -r requirements.txt

This will install PyTorch, XGBoost, statsmodels, scikit-learn, pandas, numpy, and all other required packages at their tested versions.


## Running the Project

With the virtual environment activated, run the main entry point:

    python main.py

This will execute the full pipeline including data preprocessing, LSTM and XGBoost training, SARIMA benchmark evaluation, and final model evaluation with real-unit MAE reporting.


## Model Overview

The ensemble model operates in two phases during training. In the first phase, the AttBiLSTM processes sequential demand data, learns temporal patterns through bidirectional encoding, and applies an additive attention mechanism to weight time steps by relevance before producing a prediction. In the second phase, XGBoost is fitted once per epoch on the accumulated LSTM output vectors and their corresponding residuals, learning to correct the LSTM's systematic errors from structured features such as lead time and product category.

At inference time, the LSTM produces a base prediction and XGBoost adds its residual correction to produce the final minimum inventory estimate.


## Evaluation

The model is evaluated using Mean Absolute Error in real demand units, computed by properly inverting the target normalisation via the fitted scaler. This makes results directly comparable to the SARIMA benchmark which also reports MAE and RMSE in raw units.

SARIMA benchmark results on the test set across 439 product and warehouse series:

    Mean MAE:     168.51 units
    Mean RMSE:    207.90 units
    Median MAE:     8.18 units

Ensemble model results:

    Normalised MAE (test):    0.0545
    Real-unit MAE (test):     11.48


## Deactivating the Virtual Environment

When you are done working on the project, deactivate the virtual environment with:

    deactivate


## Dependencies

All dependencies are pinned in requirements.txt. Key libraries include:

    torch             Deep learning framework for the LSTM
    xgboost           Gradient boosting for residual correction
    statsmodels       SARIMAX benchmark model
    scikit-learn      Preprocessing scalers and error metrics
    pandas            Data manipulation and time series handling
    numpy             Numerical operations
