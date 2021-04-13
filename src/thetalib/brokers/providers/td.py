import sys
import os
import http.server
import urllib.parse
import threading
import webbrowser
import json
from decimal import Decimal

import requests
import dateutil.parser

from thetalib.brokers.base import (
    AssetType,
    Broker,
    PositionEffect,
    Instruction,
    OptionType,
    Trade,
)


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
        asset_type = self._get_asset_type()
        instrument = api_object['transactionItem']['instrument']
        if asset_type == AssetType.EQUITY:
            symbol = instrument['symbol']
            option_expiration = None
        else:
            symbol = instrument['underlyingSymbol']
            option_expiration = dateutil.parser.parse(
                instrument['optionExpirationDate'])

        super().__init__(
            api_object,
            dateutil.parser.parse(api_object['transactionDate']),
            dateutil.parser.parse(api_object['orderDate']),
            dateutil.parser.parse(api_object['settlementDate']).date(),
            self._get_instruction(),
            asset_type,
            self._get_option_type(asset_type),
            self._get_position_effect(asset_type),
            self._get_fees_and_commission(),
            api_object['transactionItem']['amount'],
            Decimal(str(api_object['transactionItem']['price'])),
            symbol,
            option_expiration,
        )

    def _get_instruction(self):
        instruction = self.api_object['transactionItem']['instruction']
        if instruction == 'BUY':
            return Instruction.BUY
        return Instruction.SELL

    def _get_asset_type(self):
        atype = self.api_object['transactionItem']['instrument']['assetType']
        if atype == 'OPTION':
            return AssetType.OPTION
        return AssetType.EQUITY

    def _get_option_type(self, asset_type):
        if asset_type == AssetType.EQUITY:
            return None
        otype = self.api_object['transactionItem']['instrument']['putCall']
        if otype == 'CALL':
            return OptionType.CALL
        return OptionType.PUT

    def _get_position_effect(self, asset_type):
        if asset_type == AssetType.EQUITY:
            return None
        peffect = self.api_object['transactionItem']['positionEffect']
        if peffect == 'OPENING':
            return PositionEffect.OPEN
        return PositionEffect.CLOSE

    def _get_fees_and_commission(self):
        return sum(Decimal(str(f)) for f in self.api_object['fees'].values())


class BrokerTd(Broker):
    """
    Broker class for TD.
    """

    provider_name = "td"

    def __init__(self, access_token, test_file=None):
        super().__init__()
        self.access_token = access_token
        self._api = TdAPI(access_token)
        self._account_info = None
        self._trades = None
        self._test_data = None
        self._test_file = test_file
        if test_file is not None:
            with open(os.path.expanduser(test_file)) as f:
                self._test_data = json.loads(f.read())

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
        cdata = config["data"]
        if "file" in cdata:
            return cls(None, test_file=cdata["file"])
        return cls(cdata["access_token"])

    def to_config(self):
        if self._test_file is not None:
            config = {"file": self._test_file}
        else:
            config = {"access_token": self.access_token}
        return config

    @classmethod
    def UI_add(cls):
        print("Initializing TD")
        print("Please enter your TD API access token:")
        # (or path to test file)
        ipt = input(" >> ")
        if os.path.isfile(os.path.expanduser(ipt)):
            config = {"file": ipt}
        else:
            config = {"access_token": ipt}
        return cls.from_config({"data": config})


def _main():
    access_token = sys.argv[1]
    broker = BrokerTd(access_token, test_file=sys.argv[2])
    print("Trades:")
    print('\n'.join(str(t) for t in broker.get_trades()))


if __name__ == "__main__":
    _main()
