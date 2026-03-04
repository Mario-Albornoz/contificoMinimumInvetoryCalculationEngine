import pandas as pd
import matplotlib.pyplot as plt
from model.DataPreprocessing import DataFramePreprocessor
from pandas import DataFrame


class DataFrameVisualizer:

    def __init__(self, df: DataFrame):
        self.df:DataFrame = df.copy()
        self.df['week'] = pd.to_datetime(self.df['week'])

    def plot_total_demand_over_time(self):
        """
        Shows total weekly demand across all products and warehouses
        """

        grouped = self.df.groupby('week')['demand'].sum()

        plt.figure()
        grouped.plot()

        plt.xlabel("Week")
        plt.ylabel("Total Demand")
        plt.title("Total Weekly Demand")

        plt.show()

    def plot_demand_per_warehouse(self):
        """
        shows demand trends per warehouse
        """

        grouped = self.df.groupby(['week', 'warehouse_name'])['demand'].sum()
        pivoted = grouped.unstack()

        plt.figure()
        pivoted.plot()

        plt.xlabel("week")
        plt.ylabel("demand")
        plt.title("weekly demand per warehouse")

        plt.show()

    def plot_product_demand(self, product_id: str):
        """
        shows weekly demand for a specific product
        """

        product_df = self.df[self.df['product_id'] == product_id]

        grouped = product_df.groupby('week')['demand'].sum()

        plt.figure()
        grouped.plot()

        plt.xlabel("week")
        plt.ylabel("demand")
        plt.title(f"demand for product {product_id}")

        plt.show()

    def plot_product_warehouse_demand(self, product_id: str, warehouse_id: str):
        """
        shows weekly demand for a product in one warehouse
        """

        subset = self.df[
            (self.df['product_id'] == product_id) &
            (self.df['warehouse_contifico_id'] == warehouse_id)
        ]

        grouped = subset.groupby('week')['demand'].sum()

        plt.figure()
        grouped.plot()

        plt.xlabel("week")
        plt.ylabel("demand")
        plt.title(f"product {product_id} in warehouse {warehouse_id}")

        plt.show()

    
    def plot_demand_distribution(self):
        """
        shows histogram of weekly demand
        useful for understanding variability
        """

        plt.figure()
        self.df['demand'].hist()

        plt.xlabel("demand")
        plt.ylabel("frequency")
        plt.title("demand distribution")

        plt.show()

    def plot_top_products(self, n=10):
        """
        shows highest-demand products
        """

        grouped = (
            self.df.groupby('product_confico_id')['demand'].sum().sort_values(ascending=False).head(n)
        )

        plt.figure()
        grouped.plot(kind='bar')

        plt.xlabel("product")
        plt.ylabel("total demand")
        plt.title(f"top {n} products by demand")

        plt.show()



