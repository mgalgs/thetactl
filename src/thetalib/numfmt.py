from colorama import Fore, Style


def deltastr(num, include_sign=True, currency=False):
    """
    Returns num colored green for positive, red for negative.
    """
    if num == 0:
        return ''
    elif num > 0:
        b4 = Fore.GREEN
    elif num < 0:
        b4 = Fore.RED
    signage = '+' if include_sign else ''
    b4 += '$' if currency else ''
    numfmt = ',.0f' if currency else ''
    return f'{b4}{num:{signage}{numfmt}}{Style.RESET_ALL}'


def pdeltastr(num, include_sign=True, currency=False):
    """
    Returns empty string if num is 0, else deltastr of num wrapped in
    parens and leading space.
    """
    if num == 0:
        return ''
    return f' ({deltastr(num, include_sign=include_sign, currency=currency)})'
