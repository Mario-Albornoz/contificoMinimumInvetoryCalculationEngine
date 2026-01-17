import os
import requests
from dotenv import load_dotenv



def main():
    load_dotenv()
    print(get_data())


def get_data(request_path:str = "bodega/"):
    contifico_api_key = os.getenv("CONTIFICO_API_KEY")
    url:str = f"https://api.contifico.com/sistema/api/v1/{request_path}"
    headers:dict = {
        "Authorization": contifico_api_key,
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error:{response.status_code}")
        return None

def get_remaining_invetory_per_month():
   return None

if __name__ == '__main__':
    main()
