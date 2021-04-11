class Trade:
    """
    Represents a single trade.
    """
    def __init__(self):
        pass


class Broker:
    """
    Abstraction for interacting with broker APIs.
    """
    def get_trades(self, since=None):
        raise NotImplementedError
