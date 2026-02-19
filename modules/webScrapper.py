import os

import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class WebScrapper:
    def __init__(self, username=os.getenv("CONTIFICO_USERNAME"), password = os.getenv("CONTIFICO_PASSWORD"),  debug = False):
        self.username:str = username
        self.password:str = password
        self.company_id:str = os.getenv("COMPANY_ID")
        self.base_url:str = os.getenv("CONTIFICO_BASE_ENDPOINT")
        self.session = requests.session()
        self.logged_in: bool = False
        self.debug: bool = debug

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

    def initialize_session(self) -> tuple[str, dict]:
        login_endpoint = os.getenv("LOGIN_ENDPOINT")
        login_url = self.base_url + login_endpoint
        self._print_debug(f"Login URL: {login_url}")

        try:
            response = self.session.get(login_url)
            response.raise_for_status()
            self._print_debug(f"Login page status: {response.status_code}")
            self._print_debug(f"Cookies received: {self.session.cookies.get_dict()}")

        except requests.exceptions.RequestException as e:
            print(f"Error accessing login page: {e}")
            return None, None

        csrf_token = None
        for cookie_name in ['csrftoken', 'csrf', 'CSRF-TOKEN']:
            if cookie_name in self.session.cookies:
                csrf_token = self.session.cookies[cookie_name]
                self._print_debug(f'Found CSRF token in cookie: {csrf_token}')
                break

        login_data = {
            'username': self.username,
            'password': self.password,
        }

        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token
            self.session.headers.update({'X-CSRFToken': csrf_token})

        self.session.headers.update({
            'Referer': login_url,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://0993361712001.contifico.com',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        })

        return login_url, login_data

    def login(self) -> bool:
        login_url, login_data = self.initialize_session()

        if not login_url:
            return False

        try:
            self._print_debug(f"Attempting login with username: {self.username}")

            response = self.session.post(login_url, data=login_data, allow_redirects=True)
            self._print_debug(f"Login response status: {response.status_code}")

            try:
                login_json = response.json()
                self._print_debug(f"Login JSON response: {login_json}")

                if login_json.get('auth') == True:
                    print("✓ First Step Authentication successful")

                    empresas = login_json.get('empresas', [])
                    if empresas:
                        self._print_debug(f"Companies available: {empresas}")

                        base_url = os.getenv("CONTIFICO_BASE_ENDPOINT")

                        company_data = {'empresa': self.company_id,
                                        'username': self.username,
                                        'password': self.password,}

                        self._print_debug(f"Selecting company at: {login_url}")

                        company_response = self.session.post(
                            login_url,
                            data=company_data,
                            allow_redirects=True
                        )

                        self._print_debug(f"Company selection status: {company_response.status_code}")
                        self._print_debug(f"Company selection URL: {company_response.url}")
                        self._print_debug(f"Cookies after company selection: {self.session.cookies.get_dict()}")

                        try:
                            company_json = company_response.json()
                            self._print_debug(f"Company selection response: {company_json}")

                            if company_json.get('auth') == True or company_json.get('url_redirect'):
                                redirect_url = company_json.get('url_redirect')

                                if redirect_url:
                                    if redirect_url.startswith('/'):
                                        redirect_url = f"{base_url}{redirect_url}"

                                    self._print_debug(f"Following redirect to: {redirect_url}")
                                    final_response = self.session.get(redirect_url)
                                    self._print_debug(f"Final URL: {final_response.url}")

                                print("✓ Login and company selection successful")
                                self.logged_in = True
                                return True
                            else:
                                errors = company_json.get('errors', 'Unknown error')
                                print(f"✗ Company selection failed: {errors}")
                                return False

                        except ValueError:
                            self._print_debug(f"Company response is HTML, checking URL: {company_response.url}")

                            if 'login' not in company_response.url.lower():
                                print("✓ Login and company selection successful")
                                self.logged_in = True
                                return True
                            else:
                                with open('company_response.html', 'w', encoding='utf-8') as f:
                                    f.write(company_response.text)
                                print("✗ Company selection failed - saved response to company_response.html")
                                return False
                    else:
                        print("✓ Login successful (no company selection needed)")
                        self.logged_in = True
                        return True
                else:
                    errors = login_json.get('errors', 'Unknown error')
                    print(f"✗ Login failed: {errors}")
                    return False

            except ValueError as e:
                self._print_debug(f"JSON parse error: {e}")
                with open('login_response.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)

                if 'login' not in response.url.lower():
                    print("✓ Login successful (HTML response)")
                    self.logged_in = True
                    return True
                else:
                    print("✗ Login failed - still on login page")
                    return False

        except requests.exceptions.RequestException as e:
            print(f"Login failed: {e}")
            return False

    def download_report(self, bodega_id: str, bodega_name: str, fecha_inicio:datetime, fecha_corte:datetime):
        if not self.logged_in:
            print("Not logged in. Please login first.")
            return None
        parsed_inicial_date = self.parse_date(fecha_inicio)
        parsed_final_date = self.parse_date(fecha_corte)

        download_root_endpoint = "/sistema/reportes/saldos_disponible/?pagina=1&excel=1&excel_personalizado=&excel_saldos_por_bodega=&pdf=&consulta=1&categoria_producto_id=&"
        endpoint_params = f"fecha_inicio={parsed_inicial_date}&producto_id=&fecha_corte={parsed_final_date}&bodega_id=64035"

        download_report_url = self.base_url + download_root_endpoint + endpoint_params
        final_path = Path(f"../files/{bodega_name}")
        final_path.mkdir(parents=True, exist_ok=True)

        try:

            print(self.session.cookies.get_dict())
            print(f"making request to url:{download_report_url}")
            response = self.session.get(download_report_url)
            response.raise_for_status()

            if response.content:
                print(f"Downloaded {len(response.content)} bytes")

                filename = "report.xlsx"
                if 'Content-Disposition' in response.headers:
                    import re
                    cd = response.headers['Content-Disposition']
                    filename_match = re.findall('filename="?([^"]+)"?', cd)
                    if filename_match:
                        filename = filename_match[0]

                filepath = final_path / filename
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"✓ Saved file: {filepath}")
                return filepath

        except requests.exceptions.RequestException as e:
            print(f"File download request failed: {e}")
            return None

    def fetch_reports_by_range(self, start_date:datetime, end_date:datetime, bodegas : list):
        """
        Fetches reports weekly forom start_date to end_date
        :param start_date: start data collection from this date
        :param end_date: end of data collection date
        :param bodegas: list of warehouses with id and name
        :return:
        """

        reports = []
        current_date = start_date

        while current_date < end_date:
            week_end = min(current_date + timedelta(days=7), end_date)

            for warehouse in bodegas:
                warehouse_id = warehouse.get('codigo')
                warehouse_name = warehouse.get('nombre')
                filepath = self.download_report(bodega_name=warehouse_name, bodega_id=warehouse_id, fecha_inicio=current_date, fecha_corte=week_end)

                if filepath:
                    reports.append({
                        'bodega': warehouse_name,
                        'bodega_id': warehouse_id,
                        'fecha_inicio': current_date,
                        'fecha_corte': week_end,
                        'filepath': filepath
                    })
                else:
                    print(f'Failed to download report {warehouse_name}: {current_date} - {week_end}')

                current_date = week_end

            return reports


        return None

    def parse_date(self, date:datetime) -> str:
        return date.strftime("%d%%2F%m%%2F%Y")



ws =  WebScrapper(debug=False)
ws.login()
ws.download_report(bodega_id="BOD001", bodega_name="Bodega Village", fecha_inicio=datetime(2026, 1, 1), fecha_corte=datetime(2026, 1, 7))
