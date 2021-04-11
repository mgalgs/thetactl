import sys
import http.server
import urllib.parse
import threading
import webbrowser
import json

import requests

import brokerbase


REDIRECT_URL = "https://127.0.0.1:42068/callback"

# I'm so sorry
KEEP_RUNNING = True


def _keep_running():
    return KEEP_RUNNING


class TdAuth():
    def __init__(self, consumer_key):
        self._consumer_key = consumer_key
        super().__init__(self)

    def get_access_token(self):
        server = threading.Thread(target=self._start_server)
        server.setDaemon(True)
        server.start()

        redirect_uri = urllib.parse.quote(REDIRECT_URL)
        consumer_key = urllib.parse.quote(self._consumer_key)
        url = ("https://auth.tdameritrade.com/auth?"
               "response_type=code&"
               f"redirect_uri={redirect_uri}&"
               f"client_id={consumer_key}%40AMER.OAUTHAP"
               "&scope=AccountAccess")
        print(f"Opening {url}")
        print("Please authorize the app from your web browser")
        webbrowser.open(url)
        server.join()

    def _start_server(self):
        class Server(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if False:
                    KEEP_RUNNING = False

        address = ('', 42068)
        httpd = http.server.HTTPServer(address, Server)
        while _keep_running():
            httpd.handle_request()


def get_access_token(consumer_key):
    return TdAuth(consumer_key).get_access_token()


class TdAPI:
    def __init__(self, access_token):
        self._access_token = access_token

    def _request(self, method, path):
        headers = {"Authorization": f"Bearer {self._access_token}"}
        fn = {
            'get': requests.get,
        }[method]
        fn(path, headers=headers)

    def get(self, path):
        return self._request('get', path)


class BrokerTd(brokerbase.Broker):
    def __init__(self, access_token, test_data=None):
        self._api = TdAPI(access_token)
        self._account_info = None
        self._test_data = test_data

    @property
    def _account_id(self):
        if self._account_info is None:
            rsp = self._api.get('accounts')
            self._account_info = rsp
        return self._account_info[0]["accountId"]

    def _get_transactions(self):
        if self._test_data:
            return self._test_data
        return self._api.get(f'accounts/{self._account_id}/transactions')

    def get_trades(self, since=None):
        return self._get_transactions()


def _main():
    access_token = sys.argv[1]
    test_data = json.loads(open(sys.argv[2]).read())
    broker = BrokerTd(access_token, test_data)
    print("Trades:")
    print(broker.get_trades())


if __name__ == "__main__":
    _main()
