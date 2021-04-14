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
    print("Please make a selection:")
    for i, name in enumerate(provider_names):
        print(f"  ({i+1}) {name}")
    while True:
        idx = input(" >> ")
        try:
            idx = int(idx)
            provider = providers[provider_names[idx - 1]]
            break
        except Exception:
            print("Invalid choice")
    new_broker = provider.UI_add()
    config.merge_broker(new_broker)
    config.persist()
    print("Saved")


def cmd_analyze_options(config, rest):
def cmd_remove_broker(config, args):
    if not args.account:
        print("You must specify an account to remove with --account")
        sys.exit(1)
    config.remove_broker(args.account)
    config.persist()
    print("Saved")


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
    elif cmd == "remove-broker":
        return cmd_remove_broker(config, args)
    elif cmd == "analyze-options":
        return cmd_analyze_options(config, rest)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
