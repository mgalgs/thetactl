import sys
import argparse

from colorama import init as colorama_init

import thetalib.config
from thetalib.brokers import get_broker_providers


colorama_init()


def cmd_list_brokers(config):
    print("Brokers")
    for broker in config.brokers:
        print(f"  - {broker}")


def cmd_add_broker(config):
    print("Add broker")
    providers = get_broker_providers()
    provider_names = list(providers.keys())
    for i, name in enumerate(provider_names):
        print(f"{i+1} {name}")
    idx = input("Select broker >> ")
    try:
        idx = int(idx)
        provider = providers[provider_names[idx - 1]]
    except Exception:
        print("Invalid choice")
        sys.exit(1)
    new_broker = provider.UI_add()
    config.merge_broker(new_broker)
    config.persist()
    print("Saved")


def cmd_analyze_options(config, rest):
    parser = argparse.ArgumentParser()
    parser.add_argument("symbols", nargs="*")
    args = parser.parse_args(rest)
    print("Options profitability tracking")
    symbols = set([s.upper() for s in args.symbols])
    for broker in config.brokers:
        broker.print_options_profitability(symbols)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command",
                        help="list-brokers, add-broker, analyze-options")
    args, rest = parser.parse_known_args()
    cmd = args.command

    config = thetalib.config.get_user_config()

    if cmd == "list-brokers":
        return cmd_list_brokers(config)
    elif cmd == "add-broker":
        return cmd_add_broker(config)
    elif cmd == "analyze-options":
        return cmd_analyze_options(config, rest)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
