import pandas as pd

from sklearn.model_selection import train_test_split
from pandas import DataFrame
from modules.databaseConnector import databaseManager

def get_dataFrame() -> tuple: #returns test_df, train_df
    """
    get 
        "product_confico_id":"BQ9pdBB26H52dasdI"
        "bodega_nombre": "Bodega Principal",
        "bodega_id": "BQ9pdBB26H52d8KE",
        "cantidad": 5
        "date":"2026-02-23"
    from database for every inventory_record and place the result in a pandas dataframe and splits it into train and test dataframes
    """
    query = """
        SELECT
            p.contifico_id as product_id,
            w.name as warehouse_name,
            w.contifico_id as warehouse_contifico_id,
            ir.initial_stock as initial_stock,
            ir.final_stock as final_stock,
            pr.start_date as start_date,
        FROM  inventory_records ir,
        INNER JOIN product p ON ir.product_id = p.id
        INNER JOIN period_record pr ON ir.period_record_id = pr.id 
        INNER JOIN warehouse w ON ir.warehouse_id = w.id 
            """

    db = databaseManager(build_schema=False)
    df = pd.read_sql_query(query, db.conn)
    df['week'] = pd.to_datetime(df['start_date'])
    df = df.drop(columns=['start_date'])
    train_df, test_df = train_test_split(df, test_size=0.2)

    return train_df, test_df

def train():
    return None

