import pandas as pd
from dotenv import load_dotenv

from modules import *
from model.DataPreprocessing import DataFramePreprocessor
from model.dataVisualisation import DataFrameVisualizer
from modules.databaseConnector import databaseManager 
from modules.scripts.dataGathering import generate_dataset


def get_data_specs(df):
    print("Shape:", df.shape)
    print("\nData types:\n", df.dtypes)
    print("\nHead of DataFrame:\n", df.head())
    print("\nSummary statistics:\n", df.describe(include='all'))
    print("\nMissing values per column:\n", df.isna().sum())
    print("\nUnique values per column:\n", df.nunique())

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
    db = databaseManager(db_path="historicalInventory.db")
    load_dotenv()
    generate_dataset(db)
    return None

def main():
    load_dotenv()
    preprocessor = DataFramePreprocessor().fetch_dataframe().prepare_dataframes()

    assert preprocessor.train_df is not None
    train_df = preprocessor.train_df
    get_data_specs(train_df)

if __name__ == '__main__':
    main()

