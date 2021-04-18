from thetalib.brokers.base import (
    Broker,
    Trade,
    Instruction,
    OptionType,
    PositionEffect,
)
from thetalib.brokers.providers import *


def get_broker_providers():
    """
    Returns a dictionary mapping broker provider names to broker provider
    classes.
    """
    return {
        provider.provider_name: provider
        for provider in Broker.providers
    }
