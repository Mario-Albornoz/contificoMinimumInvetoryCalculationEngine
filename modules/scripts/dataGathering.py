from datetime import datetime, timedelta

import requests
import os

from modules.databaseConnector import databaseManager
from modules.data.webScrapper import  WebScrapper
from modules.data.reportUtils import  gather_data_from_report
from dotenv import load_dotenv

db = databaseManager(db_path="historicalInventory.db")
load_dotenv()

def gather_warehouse_data_from_api() -> list[dict]:
    contifico_api_key: str | None = os.getenv("CONTIFICO_API_KEY")
    url: str = f"https://api.contifico.com/sistema/api/v1/bodega"
    headers: dict = {
        "Authorization": contifico_api_key,
    }

    bodegas_data = []
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            for bodega in response.json():
                bodega_data = {
                    "codigo": bodega.get("codigo"),
                    "nombre": bodega.get("nombre"),
                    "contifico_id":bodega.get("id")
                }
                bodegas_data.append(bodega_data)

        else:
            print(f"Error:{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []

    return bodegas_data

def populate_warehouse_tables():
    warehouse_data = gather_warehouse_data_from_api()
    for warehouse in warehouse_data:
        db.upsert_warehouse(warehouse['nombre'],  warehouse['codigo'], warehouse['contifico_id'])
    db.execute("""
    UPDATE warehouse
    SET internal_contifico_id = 64035
    WHERE name = 'Bodega Village'
    """)
    db.execute("""
            UPDATE warehouse
            SET internal_contifico_id = 64730
            WHERE name = 'Bodega Riocentro Ceibos'
            """)
    db.execute("""
        UPDATE warehouse
        SET internal_contifico_id = 87729
        WHERE name = 'Bodega Mall del Sol'
        """)
    db.close()

def generate_data_set_with_date_range( start_date:datetime, end_date:datetime, bodegas : list):
        """
        Fetches reports weekly forom start_date to end_date
        :param start_date: start data collection from this date
        :param end_date: end of data collection date
        :param bodegas: list of warehouses with id and name
        :return:
        """
        """
            Currently we will download the reports everytime we genearte the dataset since the company is internally cleaning discontinued products
            therefore data is bound to change. Therefore for the final product we will hold not hold state in our database we will reconstructed it based
            on the reports downloaded. (further research is needed to confirm this architectural desition as of 23-03-2026)
        """
        scrapper = WebScrapper()
        reports = []
        current_date = start_date

        while current_date < end_date:
            week_end = min(current_date + timedelta(days=7), end_date)

            for warehouse in bodegas:
                warehouse_id = warehouse['internal_contifico_id']
                warehouse_name = warehouse['name']
                filepath = scrapper.download_report(bodega_name=warehouse_name, bodega_id=warehouse_id, fecha_inicio=current_date, fecha_corte=week_end)

                if filepath:
                    reports.append({
                       'bodega': warehouse_name,
                        'bodega_id': warehouse_id,
                        'fecha_inicio': current_date,
                        'fecha_corte': week_end,
                        'filepath': filepath
                    })
                    print(f'starting to gather data from file{filepath}')
                    gather_data_from_report(warehouse_id, filepath, db)

                    os.remove(filepath)
                else:
                    print(f'Failed to download report {warehouse_name}: {current_date} - {week_end}')

                current_date = week_end
                print(current_date)

        return reports

def generate_dataset():
    print('gathering stores')
    stores = db.getStoreWarehouse()
    print("populating warehouse tables")
    populate_warehouse_tables()
    print("starting to generate data set....")
    generate_data_set_with_date_range(start_date=datetime(2022, 1, 1), end_date=datetime(2026, 2, 1), bodegas=stores)
    return None

generate_dataset()
