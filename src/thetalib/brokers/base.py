import os
from dataclasses import dataclass
from enum import Enum
import datetime
from decimal import Decimal
import logging

import pytz

from thetalib import config


logging.basicConfig(
    filename=os.path.join(config.get_user_data_dir(), 'thetactl.log'),
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


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
    option_symbol: str

    @property
    def dte(self):
        now = datetime.datetime.now(pytz.utc)
        if self.option_expiration > now:
            return (self.option_expiration - now).days

    @property
    def cost(self):
        """
        price * quantity. Positive for OPEN, negative for CLOSE.
        """
        sign = -1 if self.instruction == Instruction.BUY else 1
        multiplier = 100 if self.asset_type == AssetType.OPTION else 1
        return self.price * self.quantity * sign * multiplier

    @property
    def ieffect(self):
        b_or_s = 'B' if self.instruction == Instruction.BUY else 'S'
        o_or_c = 'O' if self.position_effect == PositionEffect.OPEN \
            else 'C'
        return f'{b_or_s}/{o_or_c}'

    def __str__(self):
        if self.asset_type == AssetType.EQUITY:
            return (f"[{self.symbol}] {self.instruction} {self.quantity} "
                    f"@{self.price} {self.ieffect}")
        return (f"{self.symbol} "
                f"{self.option_expiration.date()} "
                f"{self.strike:4} {self.option_type:4} "
                f"{self.ieffect} {self.quantity}@{self.price:<6}")


class Broker:
    """
    Abstraction for interacting with broker APIs.

    Subclasses must set:

    - provider_name
    - account_name

    and must override:

    - get_trades
    - from_config
    - to_config_data
    - UI_add
    """

    providers = []

    def __init__(self):
        self._trades = None

    def __str__(self):
        return f"{self.account_name} ({self.provider_name})"

    @classmethod
    def __init_subclass__(cls):
        cls.providers.append(cls)

    def get_trades(self, symbols=None) -> list[Trade]:
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

    def to_config_data(self):
        """
        Serializes broker configuration into a config dictionary (which will be
        serialized for storage to disk by the configuration layer).
        """
        raise NotImplementedError

    @classmethod
    def UI_add(cls, account_name):
        """
        Interactively collect any configuration necessary to configure this
        broker (access token, etc.) and returns an initialized broker
        object.
        """
        raise NotImplementedError

    def get_options_trades(self, symbols=None):
        return [
            t for t in self.get_trades(symbols)
            if t.asset_type == AssetType.OPTION
        ]
