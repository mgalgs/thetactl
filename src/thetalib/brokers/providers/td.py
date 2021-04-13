import sys
import http.server
import urllib.parse
import threading
import webbrowser
import json
from decimal import Decimal

import requests
import dateutil.parser

from thetalib.brokers.base import Trade, Broker


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


class TdTrade(Trade):
    """
    Trade class for TD.
    """

    def __init__(self, api_object):
        if api_object['type'] != 'TRADE':
            raise ValueError("TdTrade only understands TRADE objects")

        self.api_object = api_object
        self.transaction_datetime = dateutil.parser.parse(
            api_object['transactionDate'])
        self.order_datetime = dateutil.parser.parse(
            api_object['orderDate'])
        self.settlement_date = dateutil.parser.parse(
            api_object['settlementDate']).date()
        self.instruction = self._get_instruction()
        self.asset_type = self._get_asset_type()
        self.option_type = self._get_option_type()
        self.position_effect = self._get_position_effect()
        self.fees_and_commissions = self._get_fees_and_commission()
        self.quantity = api_object['transactionItem']['amount']
        self.price = Decimal(str(api_object['transactionItem']['price']))

        instrument = api_object['transactionItem']['instrument']
        if self.asset_type == Trade.AssetType.EQUITY:
            self.symbol = instrument['symbol']
            self.option_expiration = None
        else:
            self.symbol = instrument['underlyingSymbol']
            self.option_expiration = dateutil.parser.parse(
                instrument['optionExpirationDate'])

    def _get_instruction(self):
        instruction = self.api_object['transactionItem']['instruction']
        if instruction == 'BUY':
            return Trade.Instruction.BUY
        return Trade.Instruction.SELL

    def _get_asset_type(self):
        atype = self.api_object['transactionItem']['instrument']['assetType']
        if atype == 'OPTION':
            return Trade.AssetType.OPTION
        return Trade.AssetType.EQUITY

    def _get_option_type(self):
        if self.asset_type == Trade.AssetType.EQUITY:
            return None
        otype = self.api_object['transactionItem']['instrument']['putCall']
        if otype == 'CALL':
            return Trade.OptionType.CALL
        return Trade.OptionType.PUT

    def _get_position_effect(self):
        if self.asset_type == Trade.AssetType.EQUITY:
            return None
        peffect = self.api_object['transactionItem']['positionEffect']
        if peffect == 'OPENING':
            return Trade.Effect.OPEN
        return Trade.Effect.CLOSE

    def _get_fees_and_commission(self):
        return sum(Decimal(str(f)) for f in self.api_object['fees'].values())


class BrokerTd(Broker):
    """
    Broker class for TD.
    """

    provider_name = "td"

    def __init__(self, access_token, test_data=None):
        super().__init__()
        self.access_token = access_token
        self._api = TdAPI(access_token)
        self._account_info = None
        self._test_data = test_data
        self._trades = None

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

    def get_trades(self):
        if self._trades is None:
            self._trades = [
                TdTrade(t)
                for t in self._get_transactions() if t['type'] == 'TRADE'
            ]
        return self._trades

    @classmethod
    def from_config(cls, config):
        return cls(
            config["data"]["access_token"],
        )

    def to_config(self):
        return {
            "access_token": self.access_token,
        }

    @classmethod
    def UI_add(cls):
        print("Initializing TD")
        print("Please enter your TD API access token:")
        access_token = input(" >> ")
        config = {
            "access_token": access_token,
        }
        return cls.from_config(config)


def _main():
    access_token = sys.argv[1]
    test_data = json.loads(open(sys.argv[2]).read())
    broker = BrokerTd(access_token, test_data)
    print("Trades:")
    print('\n'.join(str(t) for t in broker.get_trades()))


if __name__ == "__main__":
    _main()
