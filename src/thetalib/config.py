import os
import json
import appdirs


def get_user_config():
    config_dir = appdirs.user_data_dir('thetactl', 'mgalgs')
    config_path = os.path.join(config_dir, 'config.json')
    try:
        with open(config_path) as f:
            config = json.loads(f.read())
    except FileNotFoundError:
        config = {}
    return config
