import pandas as pd
import torch
from dotenv import load_dotenv
from torch.nn.modules import L1Loss

from evaluation.SARIMAbenchmark import SARIMABenchmark
from model.DataPreprocessing import DataFramePreprocessor
from model.dataVisualisation import DataFrameVisualizer
from model.evaluation import evaluate
from model.InventoryForcaster import AttBiLSTMParams, InventoryForcaster, XGBoostParams
from model.train import train
from modules import *
from modules.databaseConnector import databaseManager
from modules.scripts.dataGathering import generate_dataset


def get_data_specs(df):
    print("Shape:", df.shape)
    print("\nData types:\n", df.dtypes)
    print("\nHead of DataFrame:\n", df.head())
    print("\nSummary statistics:\n", df.describe(include="all"))
    print("\nMissing values per column:\n", df.isna().sum())
    print("\nUnique values per column:\n", df.nunique())
    print(df["demand"].describe())
    print(df["demand"].quantile([0.5, 0.75, 0.90, 0.95, 0.99]))


def show_output_from_database():
    db = databaseManager(build_schema=False)
    query = """
                                SELECT
                                    p.contifico_id as product_contifico_id,
                                    ir.initial_stock as initial_stock,
                                    ir.final_stock as final_stock,
                                    pr.start_date as start_date
                                FROM  inventory_records ir
                                LEFT JOIN product p ON ir.product_id = p.id
                                LEFT JOIN period_record pr ON ir.period_record_id = pr.id 
    """
    result = db.execute(query=query)

    df = pd.DataFrame(result, columns=[d[0] for d in db.cursor.description])
    get_data_specs(df)

    return result


def recreate_dataset():
    db = databaseManager(db_path="historicalInventory.db", build_schema=True)
    generate_dataset(db)
    return None


def viualize_data(df):
    viualizer = DataFrameVisualizer(df)
    viualizer.plot_demand_distribution()
    viualizer.plot_demand_per_warehouse()
    viualizer.plot_total_demand_over_time()
    viualizer.plot_top_products()


def get_sarimax():
    preprocesor = (
        DataFramePreprocessor(debug=False)
        .fetch_dataframe()
        .add_features()
        .encode_text_columns()
        .create_embedding()
        .split_dataset()
    )
    sarima = SARIMABenchmark(preprocessor=preprocesor)
    sarima.run()
    sarima.summary()


def run_training(preprocessor):

    train_loader, test_loader = preprocessor.get_dataloaders()
    lstm_params = AttBiLSTMParams(
        input_size=17,
        hidden_size=128,
        num_layer=2,
        output_layer=1,
    )

    xgboost_params = XGBoostParams(
        n_estimator=100,
        max_depth=6,
        learning_rate=0.1,
    )
    model = InventoryForcaster(lstm_params=lstm_params, xGradient_params=xgboost_params)
    optimizer = torch.optim.Adam(model.lstm.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer=optimizer, mode="min", factor=0.5, patience=5
    )
    criteron = L1Loss()
    history = train(
        model,
        dataloader=train_loader,
        optimizer=optimizer,
        scheduler=scheduler,
        criterion=criteron,
        epochs=100,
        device=torch.device("cpu"),
    )

    return history


def evaluate_model(preprocessor):
    print("fetching dataframe and tensors..")

    train_loader, test_loader = preprocessor.get_dataloaders()

    # model must be initialized with same params used during training
    input_size = preprocessor.train_tensor[0].shape[1]  # type: ignore
    lstm_params = AttBiLSTMParams(
        input_size=input_size,
        hidden_size=128,
        num_layer=2,
        output_layer=1,
    )
    xgboost_params = XGBoostParams(
        n_estimator=100,
        max_depth=6,
        learning_rate=0.1,
    )
    model = InventoryForcaster(lstm_params=lstm_params, xGradient_params=xgboost_params)

    # load best saved weights
    model.lstm.load_state_dict(torch.load("best_model.pt"))
    model.xgboost.load_model("best_model_xgboost.json")

    criterion = L1Loss()

    test_loss, real_error = evaluate(
        model,
        test_loader,
        criterion,
        torch.device("cpu"),
        preprocessor.standar_scaler,
    )
    print(f"Test Loss (normalized): {test_loss:.4f}")
    print(f"Test Loss (real units): {real_error:.2f} units average error")


def main():
    load_dotenv()
    preprocessor = (
        DataFramePreprocessor(debug=False)
        .fetch_dataframe()
        .add_features()
        .encode_text_columns()
        .create_embedding()
        .split_dataset()
        .pandas_df_to_tensor()
    )
    get_sarimax()
    evaluate_model(preprocessor)
    get_data_specs(preprocessor.train_df)


if __name__ == "__main__":
    main()
