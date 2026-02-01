import os

from urllib.parse import urlparse, urljoin
import requests
from datetime import datetime, timedelta
from pathlib import Path

class WebScrapper:
    def __init__(self, params:dict = None, username=os.getenv("CONTIFICO_USERNAME"), password = os.getenv("CONTIFICO_PASSWORD"), endpoint=os.getenv("CONTIFICO_DOWNLOAD_ENDPOINT")):
        self.username:str = username
        self.password:str = password
        self.endpoint:str = endpoint
        self.params:dict = params
        self.base_url:str = ""
        self.session = requests.session()
        self.logged_in: bool = False
        self.debug: bool= True

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

    def _print_debug(self, message:str):
        if self.debug:
            print(f" DEBUG: {message}")

    def login(self) -> bool:

        login_url, login_data = self.initialize_session()

        try:
            self._print_debug(f"Attempting login with username: {self.username}")
            response = self.session.post(login_url, login_data, allow_redirects= True)
            self._print_debug(f"Login response status: {response.status_code}")
            self._print_debug(f"Final URL after redirect: {response.url}")
            self._print_debug(f"Cookies after login: {self.session.cookies.get_dict()}")

            if 'login' not in response.url.lower():
                print("Login was succesful")
                return True
            else:
                print("✗ Login failed - still on login page")

                return False

        except requests.exceptions.RequestException as e:
            print(f"Loging failed: {e}")

        return False

    def initialize_session(self) -> tuple[str, dict]:
        login_url = urljoin(self.base_url, "/sistema/administracion/login/")
        self._print_debug(os.getenv("LOGIN_ENDPOINT"))

        try:
            response = self.session.get(os.getenv("LOGIN_ENDPOINT"))
            response.raise_for_status()
            self._print_debug(f"Loging status: {response.status_code}")
            self._print_debug(f" Cookies received : {self.session.cookies.get_dict()}")

        except requests.exceptions.RequestException as e:
            print(f"Error accessing login page: {e}")
            return False

        csrf_token = None
        if 'csrf' in self.session.cookies:
            csrf_token = self.session.cookies['csrf']
            self._print_debug(f'Found csrf_token {csrf_token}')

        login_data = {
            'username': self.username,
            'password': self.password,
        }

        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token
            self.session.headers.update({'X-CSRFToken': csrf_token})

        self.session.headers.update({
            'Refer': login_url,
            'Content-type': 'application/x-www-form-urlencoded',
        })

        return login_url, login_data

    def download_report(self, bodega_name:str):
        download_root_path = os.getenv("DOWNLOAD_REPORTS_ROOT_PATH")
        final_path = Path(f"../files/{bodega_name}").mkdir(exist_ok=True)

        try:
            response = requests.get(self.endpoint, auth=(self.username, self.password))
        except requests.exceptions.RequestException as e:
            print(f"file download request failed {e}")
            return None

        if response:
            print(response.content)

        #filename= "reportTest.xlsx"
        #with open(filename, "wb") as f:
        #    f.write(response.content)
        #print("saved file")


ws =  WebScrapper()
ws.login()
