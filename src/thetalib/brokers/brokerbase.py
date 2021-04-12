from dataclasses import dataclass
from enum import Enum
import datetime
from decimal import Decimal

import dateutil.parser
import pytz


@dataclass
class Trade:
    """
    Represents a single trade.
    """

    class Effect(Enum):
        OPEN = 1
        CLOSE = 2

        def __str__(self):
            return "OPEN" if self.value == Trade.Effect.OPEN else "CLOSE"

    class Instruction(Enum):
        BUY = 1
        SELL = 2

        def __str__(self):
            return "BUY" if self.value == Trade.Instruction.BUY else "SELL"

    class AssetType(Enum):
        EQUITY = 1
        OPTION = 2

        def __str__(self):
            return "EQUITY" if self.value == Trade.AssetType.EQUITY \
                else "OPTION"

    class OptionType(Enum):
        PUT = 1
        CALL = 2

        def __str__(self):
            return "PUT" if self.value == Trade.OptionType.PUT else "CALL"

    api_object: str
    transaction_datetime: datetime.datetime
    order_datetime: datetime.datetime
    settlement_date: datetime.date
    instruction: Instruction
    asset_type: AssetType
    option_type: OptionType
    position_effect: Effect
    fees_and_commissions: Decimal
    quantity: int
    price: Decimal
    symbol: str
    option_expiration: datetime.datetime

    @property
    def dte(self):
        now = datetime.datetime.now(pytz.utc)
        if self.option_expiration > now:
            return (self.option_expiration - now).days

    def __str__(self):
        if self.asset_type == Trade.AssetType.EQUITY:
            return (f"[{self.symbol}] {self.instruction} {self.quantity} "
                    f"@{self.price}")
        dte = self.dte
        ret = (f"[{self.symbol}] {self.instruction} to "
               f"{self.position_effect} @{self.price}")
        if dte is not None:
            ret += f" ({dte} DTE)"
        return ret


class Broker:
    """
    Abstraction for interacting with broker APIs.
    """

    def get_trades(self, since=None):
        raise NotImplementedError
