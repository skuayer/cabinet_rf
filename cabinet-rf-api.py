import argparse
import json

import requests


class CabinetRFAPI:
    def __init__(self, timeout=15.0):
        self.domain = 'https://xn----7sbdqbfldlsq5dd8p.xn--p1ai'
        self.timeout = timeout
        self.cookie = ''
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Language': 'en-GB,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,en-US;q=0.6',
        }

    def check_main_page(self):
        assert self.session.get(url=self.domain, headers=self.headers, timeout=self.timeout).ok

    def login(self, username, password):
        auth_form_data = {'username': username, 'password': password}

        resp = self.session.post(f"{self.domain}/api/v4/auth/login/",
                                 allow_redirects=False,
                                 data=auth_form_data,
                                 headers=self.headers,
                                 timeout=self.timeout)
        self.headers['Cookie'] = resp.headers['Set-Cookie'].split(';')[0]
        assert resp.ok, 'Ошибка авторизации'

    def get_accounts(self):
        def get_address(account_body):
            return f"""{account_body["owner"]["house"]["address"]} {account_body["owner"]["area"]["str_number"]}"""

        resp = self.session.get(f"{self.domain}/api/v4/auth/current/",
                                allow_redirects=False,
                                headers=self.headers,
                                timeout=self.timeout)
        assert resp.ok

        body = resp.json()
        current_id = body["_id"]
        current_address = get_address(body)

        return {current_id: current_address} | dict(map(lambda a: (a["_id"], get_address(a)), body["connected"]))

    def switch_account(self, account):
        resp = self.session.patch(f"{self.domain}/api/v4/auth/switch/{account}/",
                                  data=dict(),
                                  headers=self.headers,
                                  timeout=self.timeout)
        assert resp.ok, 'Ошибка смены номера счета'
        self.headers['Cookie'] = resp.headers['Set-Cookie'].split(';')[0]

    def get_meters(self):
        self.headers['Content-Type'] = 'application/json;charset=utf-8'
        resp = self.session.get(f"{self.domain}/api/v4/cabinet/meters/",
                                headers=self.headers,
                                timeout=self.timeout)
        meters = filter(lambda m: m['readonly'] == False, resp.json()['current_meters'])

        if not meters:
            raise ValueError("На этом лицевом счете нет счетчиков для передачи показаний")
        else:
            return dict(map(lambda r: (r['serial_number'], r['id']), meters))

    def send_values(self, meters, **kwargs):
        body = {
            "meters": list(map(lambda kv:
                               {
                                   "meter_id": meters[kv[0]],
                                   "values": [kv[1]]
                               }, kwargs.items()))
        }

        self.headers['Content-Type'] = 'application/json;charset=utf-8'

        resp = self.session.post(f"{self.domain}/api/v4/cabinet/meters/",
                                 data=json.dumps(body),
                                 headers=self.headers,
                                 timeout=self.timeout)
        assert resp.ok

    def logout(self):
        resp = self.session.post(f"{self.domain}/api/v4/auth/logout/", headers=self.headers, timeout=self.timeout)
        assert resp.ok


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Скрипт для отправки данных')
    parser.add_argument('action', help='Команда')
    parser.add_argument('params', nargs="*", help='Данные счетчиков')
    parser.add_argument('-u', '--username', help='Имя пользователя', required=True)
    parser.add_argument('-p', '--password', help='Пароль', required=True)
    parser.add_argument('-a', '--account', help='ID лицеовго счета')

    args = parser.parse_args()
    action = args.action
    username = args.username
    password = args.password
    account = args.account
    params = args.params

    api = CabinetRFAPI()
    try:
        api.check_main_page()
        api.login(username, password)
        if action == "accounts":
            accounts = api.get_accounts()
            print("ID л/с -> адрес:")
            for x, y in accounts.items():
                print(f"{x} ->  {y}")

        elif action == "meters":
            if account is not None:
                api.switch_account(account)
            meters = api.get_meters()
            print("Счетчики доступные для подачи показаний:")
            for x, y in meters.items():
                print(x)

        elif action == "send":
            assert len(params) % 2 == 0, "Ожидаются список пар номеров счетчиков и результатов"
            meters_and_values = dict()
            for x, y in zip(params[::2], params[1::2]):
                meters_and_values = meters_and_values | {x: y}
            if not account:
                api.switch_account(account)
            meters = api.get_meters()
            print(f"Посылаются данные счетчиков: {meters_and_values}")
            api.send_values(meters, **meters_and_values)
    finally:
        api.logout()
        print('close connection')
