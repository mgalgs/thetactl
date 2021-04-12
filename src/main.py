import sys
import argparse

import thetalib.config


def cmd_list_brokers():
    print("Brokers")


def cmd_add_broker():
    print("Add broker")


def cmd_show_options():
    config = thetalib.config.get_user_config()
    print("Show options")
    print(config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command",
                        help="list-brokers, add-broker, show-options")
    args = parser.parse_args()
    cmd = args.command
    if cmd == "list-brokers":
        return cmd_list_brokers()
    elif cmd == "add-broker":
        return cmd_add_broker()
    elif cmd == "show-options":
        return cmd_show_options()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
