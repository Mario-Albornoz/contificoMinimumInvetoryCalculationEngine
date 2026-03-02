import pandas as pd

from sklearn.model_selection import train_test_split
from pandas import DataFrame
from modules.databaseConnector import databaseManager
from sqlite.queries import get_records_for_data_frame_query  



def fetch_dataframe() -> DataFrame: #returns test_df, train_df
    """
    get 
        "product_confico_id":"BQ9pdBB26H52dasdI"
        "bodega_nombre": "Bodega Principal",
        "bodega_id": "BQ9pdBB26H52d8KE",
        "cantidad": 5
        "date":"2026-02-23"
    from database for every inventory_record and place the result in a pandas dataframe and splits it into train and test dataframes
    """
    query = get_records_for_data_frame_query
    db = databaseManager(build_schema=False)
    df = pd.read_sql_query(query, db.conn)

    return df 

def prepare_dataframes(df) -> tuple:
    df['demand'] = df['initial_stock'] - df['final_stock']
    df['week'] = pd.to_datetime(df['start_date'])
    df['week_of_year'] = df['week'].dt.isolocalendar().week
    df['month'] = df['week'].dt.month
    df = df.drop(columns=['start_date'])
    train_df = df[df['week'] < df['week'].max() - pd.Timedelta(weeks=12)]
    test_df = df[df['week'] >= df['week'].max() - pd.Timedelta(weeks=12)]

    return train_df, test_df

#TODO: Set up main training function
#TODO: Create classes for model and loss function
#TODO Implement current non ai solutions
def train():
    return None

