import sys
import argparse

from colorama import init as colorama_init

import thetalib.config
from thetalib.brokers import get_broker_providers
from thetalib.ui.components import trade_grid


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
    accname = None
    while True:
        print("Please enter a name for the new account:")
        accname = input(" >> ")
        if not config.get_broker_config_by_name(accname):
            break
        print("A broker with that name already exists. "
              "Please pick another name.")
    new_broker = provider.UI_add(accname)
    config.merge_broker(new_broker)
    config.persist()
    print("Saved")


def cmd_remove_broker(config, args):
    if not args.account:
        print("You must specify an account to remove with --account")
        sys.exit(1)
    config.remove_broker(args.account)
    config.persist()
    print("Saved")


def cmd_analyze_options(config, args, rest):
    parser = argparse.ArgumentParser()
    parser.add_argument("symbols", nargs="*")
    subargs = parser.parse_args(rest)
    print("Options profitability tracking")
    symbols = set([s.upper() for s in subargs.symbols])
    broker = None
    if args.account:
        broker = config.get_broker_by_name(args.account)
        if broker is None:
            print(f"Couldn't find broker with name {args.account}")
            print("Available broker accounts:")
            cmd_list_brokers(config)
            sys.exit(1)
    else:
        if len(config.brokers):
            broker = config.brokers[0]
        else:
            print("No brokers configured. Please use the add-broker command.")
            sys.exit(1)
    print(trade_grid(broker.get_options_trades(symbols)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command",
                        help="list-brokers, add-broker, analyze-options")
    parser.add_argument("--account")
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
        return cmd_analyze_options(config, args, rest)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
