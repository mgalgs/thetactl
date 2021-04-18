import sys
import argparse

from colorama import init as colorama_init

import thetalib.config
from thetalib.brokers import get_broker_providers
from thetalib.ui.components import trade_grid


colorama_init()
cli = argparse.ArgumentParser()
subparsers = cli.add_subparsers(dest="subcommand")


# some helpers for subcommands
# https://mike.depalatis.net/blog/simplifying-argparse.html
def fn_name_to_cmd_name(fn_name):
    return fn_name.lstrip('cmd_').replace('_', '-')


def subcommand(args=[], parent=subparsers, help=None):
    def decorator(func):
        name = fn_name_to_cmd_name(func.__name__)
        parser = parent.add_parser(name, description=func.__doc__, help=help)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)
    return decorator


def argument(*name_or_flags, **kwargs):
    return ([*name_or_flags], kwargs)


@subcommand(help="List brokers")
def cmd_list_brokers(config, args):
    print("Brokers")
    for broker in config.brokers:
        print(f"  - {broker}")


@subcommand(help="Add broker")
def cmd_add_broker(config, args):
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


@subcommand(help="Remove broker")
def cmd_remove_broker(config, args):
    if not args.account:
        print("You must specify an account to remove with --account")
        sys.exit(1)
    config.remove_broker(args.account)
    config.persist()
    print("Saved")


@subcommand([argument("symbols", nargs="*",
                      help=("Restrict report to these symbols"))],
            help="Analyze options profitability")
def cmd_analyze_options(config, args):
    print("Options profitability tracking")
    symbols = set([s.upper() for s in args.symbols])
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
    cli.add_argument("--account")
    args = cli.parse_args()
    cmd = args.subcommand
    config = thetalib.config.get_user_config()

    if cmd is None:
        cli.print_help()
    else:
        args.func(config, args)


if __name__ == "__main__":
    main()
