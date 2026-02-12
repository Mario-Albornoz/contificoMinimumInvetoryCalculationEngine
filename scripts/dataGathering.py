import openpyxl
import requests
import os

from modules.databaseConnector import databaseManager
from modules.reportUtils import extract_data_from_report, get_value_from_sheet, parse_date_string
from dotenv import load_dotenv

db = databaseManager()
db.initialize_schema()
current_file_path = '../files/ReporteSaldosDisponibles.xlsx'
load_dotenv()

def gather_warehouse_data() -> list[dict]:
    contifico_api_key = os.getenv("CONTIFICO_API_KEY")
    url: str = f"https://api.contifico.com/sistema/api/v1/bodega"
    headers: dict = {
        "Authorization": contifico_api_key,
    }

    bodegas_data = []
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(response.content)

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

def gather_data_from_report(warehouse_id:str):
    ws = set_current_workbook(current_file_path)

    date_string = get_value_from_sheet('Rango de Fechas', ws)
    products = extract_data_from_report(ws)

    if date_string:
        start_date, end_date = parse_date_string(date_string)
    else:
        print("Date range not found in the spreadsheet")

    period_id = db.insert_period_record(start_date, end_date, warehouse=warehouse_id)

    for product in products:
        product_id = db.upsert_product(product.product_name, product.product_code, unit_type=product.unit_type)
        db.insert_inventory_record(product_id, period_id, product.initial_stock, product.final_stock)

    print("dataset generated sucessfuly")


def set_current_workbook(file_path):
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    return ws

def gather_data():
    warehouse_data = gather_warehouse_data()
    for warehouse in warehouse_data:
        warehouse_id = db.upsert_warehouse(warehouse['name'],  warehouse['code'], warehouse['contifico_id'])
        gather_data_from_report(warehouse_id)
    db.close()