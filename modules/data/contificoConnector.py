import os
import requests

#TODO: Create a proper client class

class ConfiticoAPIClient:
    def __init__(self):
        self.base_url = "https://api.contifico.com/sistema/api/v2/"
        self.api_key = os.getenv("CONTIFICO_API_KEY")
        self.headers = {
        "Authorization": self.api_key
        }
        self.warehouses = WarehouseResource(self)
        self.products = ProductResource(self)

    def _get(self, endpoint_path:str, params:dict = None): #type:ignore
        url = self.base_url + endpoint_path
        response = requests.get(url, params)
        response.raise_for_status()
        return response.json()

class WarehouseResource:
    def __init__(self, client: ConfiticoAPIClient):
        self.client = client

    def gather_warehouse_data_from_api(self):
        bodegas_data = []
        response = self.client._get("bodega")
        for bodega in response:
            bodega_data = {
                        "codigo": bodega.get("codigo"),
                        "nombre": bodega.get("nombre"),
                        "contifico_id":bodega.get("id")
                    }
            bodegas_data.append(bodega_data)
        return bodegas_data

class ProductResource:
    def __init__(self, client: ConfiticoAPIClient):
        self.client = client

    def get_all_products(self):
        response = self.client._get("productos")
        return response

