import pandas as pd
import numpy as np
from sqlite.queries import get_records_for_data_frame_query

from modules.databaseConnector import databaseManager

class DataFramePreprocessor:
    def __init__(self):
        self.df  = None
        self.train_df = None
        self.test_df = None

    def fetch_dataframe(self): 
        """
        get 
            "product_confico_id":"BQ9pdBsdfwkjhaf2dasdI"
            "bodega_nombre": "Bodega Principal",
            "bodega_id": "BQ9pdBB26H52sdfseIJ",
            "cantidad": 5
            "date":"2026-02-23"
        from database for every inventory_record and place the result in a pandas dataframe and splits it into train and test dataframes
        """
        query = get_records_for_data_frame_query
        db = databaseManager(build_schema=False)
        self.df = pd.read_sql_query(query, db.conn)
        print(self.df)
    
        return self 

    def add_types_to_dataframe(self):
        numeric_colums = [
                'demand_lag_1',
                'demand_lag_4',
                'demand_lag_3',
                'demand_lag_2',
                'initial_stock', 
                'final_stock',
                'demand',
                ]

        for col in numeric_colums:
            if col in self.df.columns: #type: ignore
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce') #type: ignore

        string_columns = [
                'product_contifico_id',
                'warehouse_name',
                'product_category'
                ]

        for col in string_columns:
            if col in self.df.columns: #type: ignore
                self.df[col] = self.df[col].astype(str) #type: ignore
        
        return self
        
    
    def prepare_dataframes(self):
        assert self.df is not None
        self.add_types_to_dataframe()
        #flag outliers/negative values
        self.df['stock_discrepancy_flag'] = (
                (self.df['initial_stock'] < 0.0) | (self.df['final_stock'] < 0.0)
                ).astype(int)
        self.df['clean_intial_stock'] = self.df['initial_stock'].clip(lower = 0)
        self.df['clean_final_stock']= self.df['final_stock'].clip(lower = 0)
        #feature engineering
        self.df['demand'] = (self.df['clean_intial_stock'] - self.df['clean_final_stock']).clip(lower = 0)
        self.df['week'] = pd.to_datetime(self.df['start_date'])
        self.df['week_of_year'] = self.df['week'].dt.isocalendar().week
        self.df['month'] = self.df['week'].dt.month
        self.df = self.df.drop(columns=['start_date'])
        for time_lag in range(1, 5):
            self.df[f'demand_lag_{time_lag}'] = self.df.groupby(['product_contifico_id', 'warehouse_contifico_id'])['demand'].shift(time_lag)

        #Split dataframe
        self.train_df = self.df[self.df['week'] < self.df['week'].max() - pd.Timedelta(weeks=12)]
        self.test_df = self.df[self.df['week'] >= self.df['week'].max() - pd.Timedelta(weeks=12)]
    
        return self 
