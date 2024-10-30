import requests
import uuid
import json
from datetime import datetime


class WrongDataError(Exception):
    pass


class GigaAPI:
    def __init__(self):
        self.cert = "/home/mlrx/Загрузки/russian_trusted_root_ca_pem.crt"
        self.autorization_token = 'YmZlNGMwYWQtM2E0ZS00NzQ3LWIzMzQtZWYxN2NjNTYxODEyOmZjOWQ0ZDNlLTlhMzctNGRiMi1iNTVmLTMzMjYwNmI2MzBjZg=='    #"MDU2MzhhNmUtYWFmNi00OWI2LWIzY2MtY2U3Zjc0NDBkYTgyOjRjZjBkMzk4LTUyMWMtNDhjNS1hYjA1LWViYTA1ODRjZjYwOA=="
        self.access_token = {"token":"XXX", "expires":datetime(1900, 1, 1, 0, 0)}
        self.obtain_access_token()

    def generate_custom_uuid(self):
        original_uuid = uuid.uuid4()
        uuid_str = str(original_uuid).replace('-', '')
        formatted_uuid = f"{uuid_str[:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}-{uuid_str[16:20]}-{uuid_str[20:]}"
        return formatted_uuid

    def obtain_access_token(self):
        try:
            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            payload={
            'scope': 'GIGACHAT_API_CORP'
            }
            headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': self.generate_custom_uuid(),
            'Authorization': f'Basic {self.autorization_token}'
            }
            resp = requests.request("POST", url, headers=headers, data=payload, verify=self.cert)
            #print(resp.status_code)
            #print(resp.text)
            if resp.status_code == 200:
                response = json.loads(resp.text)
                self.access_token["token"] = response["access_token"]
                self.access_token["expires"] = datetime.fromtimestamp(response['expires_at'])
                return True
            else:
                raise WrongDataError
        except Exception as e:
            return False

    def get_models(self):
        try:
            if datetime.datetime.now() > self.access_token[1]:
                self.obtain_access_token()

            url = "https://gigachat.devices.sberbank.ru/api/v1/models"
            payload={}
            headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token[0]}'
            }
            response = requests.request("GET", url, headers=headers, data=payload, verify=self.cert)
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                raise WrongDataError
        except Exception as e:
            return f"Ошибка: {e}"

    def get_simple_answer(self, messages):
        try:
            if datetime.now() > self.access_token['expires']:
                self.obtain_access_token()
            
            url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
            payload = json.dumps({
            "model": "GigaChat-Pro",
            "messages": messages,
            "stream": False,
            "repetition_penalty": 1
            })
            headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token['token']}'
            }
            response = requests.request("POST", url, headers=headers, data=payload, verify=self.cert)
            return json.loads(response.text)
        except Exception as e:
            print(e)

def main():
    api = GigaAPI()
    print(api.obtain_access_token())