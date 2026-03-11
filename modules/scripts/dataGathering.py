import os
from datetime import datetime, timedelta

from modules.data.reportUtils import gather_data_from_report
from modules.data.webScrapper import WebScrapper
from modules.databaseConnector import databaseManager


def generate_data_set_with_date_range(
    db: databaseManager, start_date: datetime, end_date: datetime, bodegas: list
):
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
            warehouse_id = warehouse["id"]
            warehouse_internal_contifico_id = warehouse["internal_contifico_id"]
            warehouse_name = warehouse["name"]
            filepath = scrapper.download_report(
                bodega_name=warehouse_name,
                bodega_internal_contifico_id=warehouse_internal_contifico_id,
                fecha_inicio=current_date,
                fecha_corte=week_end,
            )

            if filepath:
                reports.append(
                    {
                        "bodega": warehouse_name,
                        "bodega_id": warehouse_id,
                        "fecha_inicio": current_date,
                        "fecha_corte": week_end,
                        "filepath": filepath,
                    }
                )
                print(f"starting to gather data from file{filepath}")
                gather_data_from_report(warehouse_id, filepath, db)

                os.remove(filepath)
            else:
                print(
                    f"Failed to download report {warehouse_name}: {current_date} - {week_end}"
                )

        current_date = week_end
        print(current_date)

    db.enrich_products_with_contifico_id()

    return reports


def generate_dataset(db):
    print("gathering stores")
    stores = db.getStoreWarehouse()
    print("starting to generate data set....")
    generate_data_set_with_date_range(
        db=db,
        start_date=datetime(2022, 1, 1),
        end_date=datetime(2026, 2, 1),
        bodegas=stores,
    )
    return None
