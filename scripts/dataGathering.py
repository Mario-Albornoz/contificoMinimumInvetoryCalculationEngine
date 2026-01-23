import openpyxl

from modules.databaseConnector import databaseManager
from modules.reportUtils import extract_data_from_report, get_value_from_sheet, parse_date_string

db = databaseManager()
db.initialize_schema()
current_file_path = '../files/ReporteSaldosDisponibles.xlsx'


def gather_data():
    ws = set_current_workbook(current_file_path)

    date_string = get_value_from_sheet('Rango de Fechas', ws)
    bodega_string = get_value_from_sheet('Bodega', ws)
    products = extract_data_from_report(ws)

    if date_string:
        start_date, end_date = parse_date_string(date_string)
    else:
        print("Date range not found in the spreadsheet")

    if bodega_string:
        bodega = bodega_string.split(':')[1].strip()
    else:
        print('Bodega not found in spreadsheet')

    period_id = db.insert_period_record(start_date, end_date, warehouse=bodega)

    for product in products:
        product_id = db.upsert_product(product.product_name, product.product_code, unit_type=product.unit_type)
        db.insert_inventory_record(product_id, period_id, product.inicial_stock, product.final_stock)

    print("dataset generated sucessfuly")


def set_current_workbook(file_path):
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    return ws


gather_data()
db.close()