import openpyxl

from databaseConnector import databaseManager
from product import ProductData

db = databaseManager()
db.initialize_schema()
file_path = 'files/ReporteSaldosDisponibles.xlsx'
wb = openpyxl.load_workbook(file_path)
ws = wb.active


def gather_data():
    date_string = None

    for row in ws.iter_rows(min_row=1, max_row=5, min_col=1, max_col=10):
        for cell in row:
            if cell.value and 'Rango de Fechas' in str(cell.value):
                date_string = str(cell.value)
                break
        if date_string:
            break

    if date_string:
        date_part = date_string.split(':')[1].strip()
        dates = date_part.split(' - ')
        start_date = dates[0].strip()
        end_date = dates[1].strip()
    else:
        print("Date range not found in the spreadsheet")

    headers = [cell.value for cell in ws[6]]
    products = []
    for row in ws.iter_rows(min_row = 1, values_only = True):
        product_code_idx = headers.index('Código')
        product_name_idx = headers.index('Nombre')
        inicial_stock_idx = headers.index('Inicial')
        final_stock_idx = headers.index('Stock Final')
        unit_type_idx = headers.index('Unidad')

        product = ProductData(
            product_code=row[product_code_idx],
            product_name = row[product_name_idx],
            inicial_stock = row[inicial_stock_idx],
            final_stock = row[final_stock_idx],
            unit_type=row[unit_type_idx]
        )

        products.append(product)

gather_data()
db.close()