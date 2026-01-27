from modules.product import ProductData

def extract_data_from_report(ws):
    headers = [cell.value for cell in ws[6]]
    products = []
    for row in ws.iter_rows(min_row=7, values_only=True):
        product_code_idx = headers.index('Código')
        product_name_idx = headers.index('Nombre')
        initial_stock_idx = headers.index('Inicial')
        final_stock_idx = headers.index('Stock Final')
        unit_type_idx = headers.index('Unidad')

        product = ProductData(
            product_code=row[product_code_idx],
            product_name=row[product_name_idx],
            initial_stock=row[initial_stock_idx],
            final_stock=row[final_stock_idx],
            unit_type=row[unit_type_idx]
        )
        print(product)

        products.append(product)
    return products

def get_value_from_sheet(value_string:str, ws):
    found_value = None
    for row in ws.iter_rows(min_row=1, max_row=5, min_col=1, max_col=10):
        for cell in row:
            if cell.value and value_string in str(cell.value):
                found_value = str(cell.value)
                break
        if found_value:
            break
    return found_value

def parse_date_string(date_string):
    date_part = date_string.split(':')[1].strip()
    dates = date_part.split(' - ')
    start_date = dates[0].strip()
    end_date = dates[1].strip()

    return start_date, end_date
