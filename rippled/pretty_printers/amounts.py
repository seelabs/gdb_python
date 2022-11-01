from rippled.pretty_printers.printers import *
from rippled.pretty_printers.printers import _register_printer

import re
import decimal

# set to False to print all digits, True to print 2 decimal places
PRETTY_AMOUNT = False


def _to_decimal(sign, value, exponent):
    # Decimal want a tuple of digits, use this ugly hack
    # until I think of a better way
    value_tuple = tuple(int(d) for d in tuple(f"{value:d}"))
    return decimal.Decimal((sign, value_tuple, exponent))


@_register_printer
class STAmount:
    "Pretty printer for STAmount"
    printer_name = "STAmount"
    version = "1.0"
    type_name_re = "^ripple::STAmount$"

    def __init__(self, value):
        self.value = value

    def to_py_value(self):
        return self.to_string()

    def to_string(self):
        sign = int(self.value["mIsNegative"])
        value = int(self.value["mValue"])
        exponent = -6 if int(self.value["mIsNative"]) else int(self.value["mOffset"])
        d = _to_decimal(sign, value, exponent)
        if PRETTY_AMOUNT and d >= 1:
            amt_str = f"{d:.2f}"
        else:
            amt_str = f"{d}"
        return f"{amt_str}/{self.value['mIssue']}"


@_register_printer
class IOUAmount:
    "Pretty printer for IOUAmount"
    printer_name = "IOUAmount"
    version = "1.0"
    type_name_re = "^ripple::IOUAmount$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        value = int(self.value["mantissa_"])
        sign = 0
        if value < 0:
            value = -value
            sign = 1
        exponent = int(self.value["exponent_"])
        d = _to_decimal(sign, value, exponent)
        if PRETTY_AMOUNT and d >= 1:
            amt_str = f"{d:.2f}"
        else:
            amt_str = f"{d}"
        return f"{amt_str}/IOU"


@_register_printer
class XRPAmount:
    "Pretty printer for XRPAmount"
    printer_name = "XRPAmount"
    version = "1.0"
    type_name_re = "^ripple::XRPAmount$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        value = int(self.value["drops_"])
        sign = 0
        if value < 0:
            value = -value
            sign = 1
        exponent = -6
        d = _to_decimal(sign, value, exponent)
        if PRETTY_AMOUNT and d >= 1:
            amt_str = f"{d:.2f}"
        else:
            amt_str = f"{d}"
        return f"{amt_str}/XRP"


@_register_printer
class Issue:
    "Pretty printer for Issue"
    printer_name = "Issue"
    version = "1.0"
    type_name_re = "^ripple::Issue$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        return f"{self.value['currency']}/{self.value['account']}"
