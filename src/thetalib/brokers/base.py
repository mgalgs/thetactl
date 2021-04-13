import os
from dataclasses import dataclass
from enum import Enum
import datetime
from decimal import Decimal
from collections import defaultdict
import logging

import pytz
from tabulate import tabulate
from colorama import init as colorama_init, Fore, Back, Style

from thetalib import config


logging.basicConfig(
    filename=os.path.join(config.get_user_data_dir(), 'thetactl.log'),
    level=logging.INFO,
)

logger = logging.getLogger(__name__)
colorama_init()


class PositionEffect(Enum):
    OPEN = 1
    CLOSE = 2

    def __str__(self):
        return "OPEN" if self == PositionEffect.OPEN else "CLOSE"


class Instruction(Enum):
    BUY = 1
    SELL = 2

    def __str__(self):
        return "BUY" if self == Instruction.BUY else "SELL"


class AssetType(Enum):
    EQUITY = 1
    OPTION = 2

    def __str__(self):
        return "EQUITY" if self == AssetType.EQUITY \
            else "OPTION"


class OptionType(Enum):
    PUT = 1
    CALL = 2

    def __str__(self):
        return "PUT" if self == OptionType.PUT else "CALL"


@dataclass
class Trade:
    """
    Represents a single trade.
    """

    api_object: str
    transaction_datetime: datetime.datetime
    order_datetime: datetime.datetime
    settlement_date: datetime.date
    instruction: Instruction
    asset_type: AssetType
    option_type: OptionType
    position_effect: PositionEffect
    fees_and_commissions: Decimal
    quantity: int
    price: Decimal
    symbol: str
    option_expiration: datetime.datetime
    strike: Decimal

    @property
    def dte(self):
        now = datetime.datetime.now(pytz.utc)
        if self.option_expiration > now:
            return (self.option_expiration - now).days

    def __str__(self):
        if self.asset_type == AssetType.EQUITY:
            return (f"[{self.symbol}] {self.instruction} {self.quantity} "
                    f"@{self.price}")
        return (f"[{self.symbol} {self.strike} {self.option_type}] "
                f"{self.instruction} to "
                f"{self.position_effect} {self.quantity}@{self.price}")


class Broker:
    """
    Abstraction for interacting with broker APIs.

    Subclasses must set:

    - provider_name

    and must override:

    - get_trades
    - from_config
    - to_config
    - UI_add
    """

    providers = []

    def __init__(self):
        self._trades = None

    def __str__(self):
        return self.provider_name

    @classmethod
    def __init_subclass__(cls):
        cls.providers.append(cls)

    def get_trades(self) -> Trade:
        """
        Returns a list of Trade objects for this broker. Caching in subclasses
        is recommended.
        """
        raise NotImplementedError

    @classmethod
    def from_config(cls, config):
        """
        Converts a config dictionary (deserialized from the configuration
        layer) into a broker object.
        """
        raise NotImplementedError

    def to_config(self):
        """
        Serializes broker configuration into a config dictionary (which will be
        serialized for storage to disk by the configuration layer).
        """
        raise NotImplementedError

    @classmethod
    def UI_add(cls):
        """
        Interactively collect any configuration necessary to configure this
        broker (access token, etc.) and returns an initialized broker
        object.
        """
        raise NotImplementedError

    def print_options_profitability(self, symbols=None):
        options_trades = [
            t for t in self.get_trades()
            if t.asset_type == AssetType.OPTION
        ]
        by_symbol = defaultdict(list)
        for t in options_trades:
            if symbols and t.symbol not in symbols:
                continue
            by_symbol[t.symbol].append(t)
        for symbol, trades in sorted(by_symbol.items(), key=lambda el: el[0]):
            print_wheel_sequence_for_symbol(symbol, trades)
            print()


def deltastr(num, include_sign=True, currency=False):
    """
    Returns num colored green for positive, red for negative.
    """
    if num == 0:
        return ''
    elif num > 0:
        b4 = Fore.GREEN
    elif num < 0:
        b4 = Fore.RED
    signage = '+' if include_sign else ''
    b4 += '$' if currency else ''
    return f'{b4}{num:{signage}}{Style.RESET_ALL}'


def pdeltastr(num, include_sign=True, currency=False):
    """
    Returns empty string if num is 0, else deltastr of num wrapped in
    parens and leading space.
    """
    if num == 0:
        return ''
    return f' ({deltastr(num, include_sign=include_sign, currency=currency)})'


def print_wheel_sequence_for_symbol(symbol: str, trades: list[Trade]):
    trades = sorted(trades, key=lambda t: t.transaction_datetime)

    print(f"{Style.BRIGHT}{symbol}{Style.RESET_ALL}")

    call_short_interest = 0
    put_short_interest = 0
    call_long_interest = 0
    put_long_interest = 0
    call_profits = 0
    put_profits = 0
    rows = []
    for trade in trades:
        call_long_interest_delta = 0
        call_short_interest_delta = 0
        call_profits_delta = 0
        put_long_interest_delta = 0
        put_short_interest_delta = 0
        put_profits_delta = 0
        pos = (trade.instruction, trade.option_type, trade.position_effect)
        if pos == (Instruction.BUY, OptionType.CALL, PositionEffect.OPEN):
            call_long_interest_delta = 100 * trade.quantity
            call_profits_delta = -trade.price * trade.quantity * 100
        elif pos == (Instruction.BUY, OptionType.CALL, PositionEffect.CLOSE):
            call_short_interest_delta = -100 * trade.quantity
            call_profits_delta = -trade.price * trade.quantity * 100
        elif pos == (Instruction.BUY, OptionType.PUT, PositionEffect.OPEN):
            put_long_interest_delta = 100 * trade.quantity
            put_profits_delta = -trade.price * trade.quantity * 100
        elif pos == (Instruction.BUY, OptionType.PUT, PositionEffect.CLOSE):
            put_short_interest_delta = -100 * trade.quantity
            put_profits_delta = -trade.price * trade.quantity * 100
        elif pos == (Instruction.SELL, OptionType.CALL, PositionEffect.OPEN):
            call_short_interest_delta = 100 * trade.quantity
            call_profits_delta = trade.price * trade.quantity * 100
        elif pos == (Instruction.SELL, OptionType.CALL, PositionEffect.CLOSE):
            call_long_interest_delta = -100 * trade.quantity
            call_profits_delta = trade.price * trade.quantity * 100
        elif pos == (Instruction.SELL, OptionType.PUT, PositionEffect.OPEN):
            put_short_interest_delta = 100 * trade.quantity
            put_profits_delta = trade.price * trade.quantity * 100
        elif pos == (Instruction.SELL, OptionType.PUT, PositionEffect.CLOSE):
            put_long_interest_delta = -100 * trade.quantity
            put_profits_delta = trade.price * trade.quantity * 100

        call_long_interest += call_long_interest_delta
        call_short_interest += call_short_interest_delta
        put_long_interest += put_long_interest_delta
        put_short_interest += put_short_interest_delta
        call_profits += call_profits_delta
        put_profits += put_profits_delta
        total_profits = call_profits + put_profits
        total_profits_delta = call_profits_delta + put_profits_delta

        rows.append((
            str(trade),
            f"{call_long_interest}{pdeltastr(call_long_interest_delta)}",
            f"{call_short_interest}{pdeltastr(call_short_interest_delta)}",
            f"{put_long_interest}{pdeltastr(put_long_interest_delta)}",
            f"{put_short_interest}{pdeltastr(put_short_interest_delta)}",
            f"{call_profits}{pdeltastr(call_profits_delta, include_sign=False, currency=True)}",
            f"{put_profits}{pdeltastr(put_profits_delta, include_sign=False, currency=True)}",
            f"{total_profits}{pdeltastr(total_profits_delta, include_sign=False, currency=True)}",
        ))

    headers = (
        "Trade",
        "Long Calls",
        "Short Calls",
        "Long Puts",
        "Short Puts",
        "Calls Profits",
        "Puts Profits",
        "Total Options Profits",
    )
    print(tabulate(rows, headers=headers, tablefmt="orgtbl"))

    call_open_interest = call_long_interest - call_short_interest
    if call_open_interest > 0:
        coi_color = Fore.GREEN
    elif call_open_interest == 0:
        coi_color = Style.RESET_ALL
    else:
        coi_color = Fore.RED
    coi = f"{coi_color}{call_open_interest}{Style.RESET_ALL}"

    put_open_interest = put_long_interest - put_short_interest
    if put_open_interest > 0:
        poi_color = Fore.GREEN
    elif call_open_interest == 0:
        poi_color = Style.RESET_ALL
    else:
        poi_color = Fore.RED
    poi = f"{poi_color}{put_open_interest}{Style.RESET_ALL}"

    print(f"{Style.BRIGHT}{symbol} Summary{Style.RESET_ALL}: "
          f"Open Call Interest={coi}, "
          f"Open Put Interest={poi}, "
          f"Total profits={deltastr(total_profits, currency=True)}")
