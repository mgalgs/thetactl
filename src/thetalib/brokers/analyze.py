import datetime
from collections import defaultdict
import typing

from colorama import Fore, Style
from tabulate import tabulate

from thetalib.brokers.base import (
    Instruction,
    OptionType,
    PositionEffect,
    Trade,
)
from thetalib.numfmt import deltastr, pdeltastr


def get_trade_grid(
        symbol: str, trades: list[Trade]) -> typing.Tuple[str, str]:

    rows = []
    total_profits = 0
    for trade in trades:
        call_long_interest_delta = 0
        call_short_interest_delta = 0
        call_profits_delta = 0
        put_long_interest_delta = 0
        put_short_interest_delta = 0
        put_profits_delta = 0
        pos = (trade.instruction, trade.option_type, trade.position_effect)
        if pos == (Instruction.BUY, OptionType.CALL, PositionEffect.OPEN):
            call_long_interest_delta = 100 * trade.quantity
            call_profits_delta = -trade.price * trade.quantity * 100
        elif pos == (Instruction.BUY, OptionType.CALL, PositionEffect.CLOSE):
            call_short_interest_delta = -100 * trade.quantity
            call_profits_delta = -trade.price * trade.quantity * 100
        elif pos == (Instruction.BUY, OptionType.PUT, PositionEffect.OPEN):
            put_long_interest_delta = 100 * trade.quantity
            put_profits_delta = -trade.price * trade.quantity * 100
        elif pos == (Instruction.BUY, OptionType.PUT, PositionEffect.CLOSE):
            put_short_interest_delta = -100 * trade.quantity
            put_profits_delta = -trade.price * trade.quantity * 100
        elif pos == (Instruction.SELL, OptionType.CALL, PositionEffect.OPEN):
            call_short_interest_delta = 100 * trade.quantity
            call_profits_delta = trade.price * trade.quantity * 100
        elif pos == (Instruction.SELL, OptionType.CALL, PositionEffect.CLOSE):
            call_long_interest_delta = -100 * trade.quantity
            call_profits_delta = trade.price * trade.quantity * 100
        elif pos == (Instruction.SELL, OptionType.PUT, PositionEffect.OPEN):
            put_short_interest_delta = 100 * trade.quantity
            put_profits_delta = trade.price * trade.quantity * 100
        elif pos == (Instruction.SELL, OptionType.PUT, PositionEffect.CLOSE):
            put_long_interest_delta = -100 * trade.quantity
            put_profits_delta = trade.price * trade.quantity * 100

        total_profits += call_profits_delta + put_profits_delta
        total_profits_delta = call_profits_delta + put_profits_delta

        rows.append((
            str(trade),
            f"{pdeltastr(call_long_interest_delta)}",
            f"{pdeltastr(call_short_interest_delta)}",
            f"{pdeltastr(put_long_interest_delta)}",
            f"{pdeltastr(put_short_interest_delta)}",
            f"{pdeltastr(call_profits_delta, include_sign=False, currency=True)}",
            f"{pdeltastr(put_profits_delta, include_sign=False, currency=True)}",
            f"{total_profits}"
            f"{pdeltastr(total_profits_delta, include_sign=False, currency=True)}",
        ))

    headers = (
        "Trade",
        "Long Calls",
        "Short Calls",
        "Long Puts",
        "Short Puts",
        "Calls Profits",
        "Puts Profits",
        "Total Profits",
    )
    table = tabulate(rows, headers=headers, tablefmt="orgtbl")
    return table, total_profits


def get_trade_sequence(
        symbol: str, trades: list[Trade]) -> str:
    trades_by_option = defaultdict(list)

    for trade in trades:
        trades_by_option[trade.option_symbol].append(trade)

    rows = []
    total_profit = 0
    for option_symbol, otrades in trades_by_option.items():
        trade_sequence = []
        profit = 0
        interest = 0
        option_expiration = otrades[0].option_expiration
        for trade in otrades:
            profit += trade.cost
            pos = (trade.instruction, trade.position_effect)
            if pos == (Instruction.BUY, PositionEffect.OPEN):
                interest += trade.quantity * 100
            elif pos == (Instruction.BUY, PositionEffect.CLOSE):
                interest += trade.quantity * 100
            elif pos == (Instruction.SELL, PositionEffect.OPEN):
                interest -= trade.quantity * 100
            elif pos == (Instruction.SELL, PositionEffect.CLOSE):
                interest -= trade.quantity * 100

            if trade.position_effect == PositionEffect.OPEN:
                effect = Fore.RED
            else:
                effect = Fore.GREEN
            trade_sequence.append(
                f"{effect}{trade.ieffect} "
                f"{trade.quantity}x{trade.price}={trade.cost}"
                f"{Style.RESET_ALL}"
            )

        total_profit += profit
        seq = ' -> '.join(trade_sequence)
        profit_s = deltastr(profit, currency=True)
        interest_s = ''
        if interest != 0:
            if option_expiration.date() > datetime.date.today():
                interest_s = f", open interest={deltastr(interest)}"
                profit_s = f"{Style.DIM}{profit_s}{Style.RESET_ALL}"
                seq += f' -> {Style.BRIGHT}...{Style.RESET_ALL}'
            else:
                seq += f' -> {Style.DIM}expired{Style.RESET_ALL}'

        rows.append(f"{option_symbol} [profit={profit_s}{interest_s}] :: "
                    f"{seq}")

    summary = f"Total profit: {deltastr(total_profit, currency=True)}"
    return summary, '\n'.join(rows)
