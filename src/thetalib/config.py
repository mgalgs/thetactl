import os
import json
import appdirs
import errno


"""

User configuration is stored in a json file with the following rough
format (TODO: make a proper schema definition):

{
  'brokers': [{
    'provider': 'td',
    'data': ... # provider-specific storage
  }, ...]
}
"""


class UserConfig:
    """
    User configuration serialization/deserialization.

    - brokers :: List of Broker objects parsed and initialized from the
    saved config.
    """

    @staticmethod
    def _get_config_path():
        config_dir = get_user_data_dir()
        return os.path.join(config_dir, 'config.json')

    def __init__(self):
        from thetalib.brokers import get_broker_providers

        self._config_path = self._get_config_path()

        try:
            os.makedirs(os.path.dirname(self._config_path))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        try:
            with open(self._config_path) as f:
                self.data = json.loads(f.read())
        except FileNotFoundError:
            self.data = {'brokers': []}

        providers = get_broker_providers()
        self.brokers = []
        for broker_cfg in self.data['brokers']:
            provider = providers.get(broker_cfg['provider'])
            if provider:
                self.brokers.append(provider.from_config(broker_cfg))

    def persist(self):
        with open(self._config_path, 'w+') as f:
            f.write(json.dumps(self.data))

    def get_broker_config_by_name(self, name):
        for broker_cfg in self.data['brokers']:
            if broker_cfg['name'] == name:
                return broker_cfg

    def get_broker_by_name(self, name):
        for broker in self.brokers:
            if broker.account_name == name:
                return broker

    def merge_broker(self, broker):
        self.data['brokers'].append({
            'provider': broker.provider_name,
            'name': broker.account_name,
            'data': broker.to_config(),
        })

    def remove_broker(self, account_name):
        newbrokers = []
        for broker_cfg in self.data['brokers']:
            if broker_cfg['name'] != account_name:
                newbrokers.append(broker_cfg)
        self.data['brokers'] = newbrokers


def get_user_config():
    return UserConfig()


def get_user_data_dir():
    return appdirs.user_data_dir('thetactl', 'mgalgs')
