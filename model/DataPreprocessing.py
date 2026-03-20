# type: ignore[reportOptionalSubscript, reportOptionalMemberAccess, reportArgumentType, reportAssignmentType, reportOptionalCall, reportOptionalIterable]
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import LabelEncoder

from modules.databaseConnector import databaseManager
from sqlite.queries import get_records_for_data_frame_query


class DataFramePreprocessor:
    def __init__(self, debug: bool = False):
        self.df = None
        self.train_df = None
        self.train_tensor = None
        self.test_df = None
        self.test_tensor = None
        self.le: LabelEncoder | None = None
        self.string_columns = [
            "product_contifico_id",
            "warehouse_name",
            "product_category",
            "product_contifico_id",
            "product_unit_type",
            "product_name",
            "product_category",
            "warehouse_name",
            "warehouse_contifico_id",
        ]
        self.numeric_colums = [
            "demand_lag_1",
            "demand_lag_4",
            "demand_lag_3",
            "demand_lag_2",
            "initial_stock",
            "final_stock",
            "demand",
        ]
        self.debug = debug

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
        if self.debug:
            print("fetching data from database...")

        query = get_records_for_data_frame_query
        db = databaseManager(build_schema=False)
        self.df = pd.read_sql_query(query, db.conn)
        print(self.df)

        return self

    def add_features(self):
        if self.debug:
            print("preprocessing data...")
        self.df["stock_discrepancy_flag"] = (
            (self.df["initial_stock"] < 0.0) | (self.df["final_stock"] < 0.0)
        ).astype(int)
        self.df["clean_initial_stock"] = self.df["initial_stock"].clip(lower=0)
        self.df["clean_final_stock"] = self.df["final_stock"].clip(lower=0)

        # feature engineering
        self.df["demand"] = (
            self.df["clean_initial_stock"] - self.df["clean_final_stock"]
        ).clip(lower=0)
        self.df["week"] = pd.to_datetime(self.df["start_date"])
        self.df["week_of_year"] = self.df["week"].dt.isocalendar().week.astype("int32")
        self.df["month"] = self.df["week"].dt.month
        self.df = self.df.drop(columns=["start_date"])

        for time_lag in range(1, 5):
            self.df[f"demand_lag_{time_lag}"] = self.df.groupby(
                ["product_contifico_id", "warehouse_contifico_id"]
            )["demand"].shift(time_lag)

        self.df = self.df.dropna()
        return self

    def split_dataset(self, weeks: int = 12):
        # splits pandas dataframe to test and train dataframes
        self.train_df = self.df[
            self.df["week"] < self.df["week"].max() - pd.Timedelta(weeks=weeks)
        ]
        self.test_df = self.df[
            self.df["week"] >= self.df["week"].max() - pd.Timedelta(weeks=weeks)
        ]

        # Week was only needed for the splitting so dropping it now is ok
        cols_to_drop = ["week"]
        self.train_df = self.train_df.drop(
            columns=[c for c in cols_to_drop if c in self.train_df.columns]
        )
        self.test_df = self.test_df.drop(
            columns=[c for c in cols_to_drop if c in self.test_df.columns]
        )

        return self

    def encode_text_columns(self):
        if self.debug:
            print("encoding text columns...")

        self.label_encoders: dict[str, LabelEncoder] = {}
        for column in self.string_columns:
            le = LabelEncoder()
            self.df[column] = le.fit_transform(self.df[column])
            self.label_encoders[column] = le

        if self.debug:
            print(self.df.dtypes)

        return self

    def add_types_to_dataframe(self):
        if self.debug:
            print("adding types to dataframe...")

        for col in self.numeric_colums:
            if col in self.df.columns:  # type: ignore
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")  # type: ignore

        for col in self.string_columns:
            if col in self.df.columns:  # type: ignore
                self.df[col] = self.df[col].astype(str)  # type: ignore
        if self.debug:
            print(self.df.dtypes)

        return self

    def create_embedding(self):
        self.embedding_dims = {
            column: (
                self.df[column].nunique(),
                min(50, (self.df[column].nunique() + 1) // 2),
            )
            for column in self.string_columns
        }

        self.embeddings = nn.ModuleDict(
            {
                column: nn.Embedding(num_embeddings, embedding_dim)
                for column, (
                    num_embeddings,
                    embedding_dim,
                ) in self.embedding_dims.items()
            }
        )

        return self

    def pandas_df_to_tensor(self):
        if self.debug:
            print("converting from pandas df to tensor")
            print(self.train_df.dtypes)
            print(self.test_df.dtypes)

        if self.train_df is None or self.test_df is None:
            raise ValueError("train or test dataframe == None")

        if self.debug:
            object_cols = self.train_df.select_dtypes(
                include=["object"]
            ).columns.to_list()

            if object_cols:
                print(f"WARNING object type still remaining: {object_cols}")

        self.train_tensor = torch.from_numpy(self.train_df.to_numpy()).float()
        self.test_tensor = torch.from_numpy(self.test_df.to_numpy()).float()
        return self
