from rippled.pretty_printers.printers import *
from rippled.pretty_printers.printers import _register_printer
from rippled.pretty_printers.printers import printer_gen
from rippled.pretty_printers.base_uint import BaseUInt
from rippled.pretty_printers.amounts import STAmount

import re
import json
from libstdcxx.v6.printers import StdVectorPrinter


@_register_printer
class SField:
    "Pretty printer for ripple::SField"
    printer_name = "SField"
    version = "1.0"
    type_name_re = "^ripple::SField$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        return str(self.value["fieldName"])[1:-1]


@_register_printer
class STVar:
    "Pretty printer for ripple::detail::STVar"
    printer_name = "STVar"
    version = "1.0"
    type_name_re = "^ripple::detail::STVar$"

    def __init__(self, value):
        self.value = value
        self.proxy_value = self.value["p_"].dereference()
        self.proxy_printer = printer_gen(self.proxy_value)

    def to_py_value(self):
        if self.proxy_printer is None:
            return f"No printer for type: {str(self.proxy_value.dynamic_type)}"
        return self.proxy_printer.to_py_value()

    def fname(self):
        return SField(self.proxy_value["fName"].dereference()).to_string()

    def is_empty(self):
        return (
            self.proxy_printer
            and isinstance(self.proxy_printer, STBase)
            and self.proxy_printer.is_empty()
        )

    def to_string(self):
        if self.proxy_printer is None:
            return self.proxy_value
        return self.proxy_printer.to_string()


@_register_printer
class STBase:
    "Pretty printer for ripple::STBase"
    printer_name = "STBase"
    version = "1.0"
    type_name_re = "^ripple::STBase$"

    def __init__(self, value):
        self.value = value.cast(value.dynamic_type)

    def is_empty(self):
        return self.value.dynamic_type.tag == "ripple::STBase"

    def to_py_value(self):
        dt = self.value.dynamic_type
        if dt.tag.startswith("ripple::STInteger"):
            return STInteger(self.value).to_py_value()
        if dt.tag.startswith("ripple::STBitString"):
            return STBitString(self.value).to_py_value()
        sf = SField(self.value["fName"].dereference()).to_string()
        match dt.tag:
            case "ripple::STBase":
                return "Not Present"
            case "ripple::STAccount":
                return STAccount(self.value).to_py_value()
            case "ripple::STAmount":
                return STAmount(self.value).to_py_value()
            case "ripple::STObject":
                return STObject(self.value).to_py_value()
        return f"No STBase subprinter for {dt.tag}"

    def to_string(self):
        return f"{self.to_py_value()}"


@_register_printer
class STInteger:
    "Pretty printer for ripple::STInteger"
    printer_name = "STInteger"
    version = "1.0"
    type_name_re = "^ripple::STInteger<.*>$"

    def __init__(self, value):
        self.value = value

    def to_py_value(self):
        return int(self.value["value_"])

    def to_string(self):
        return f'{self.value["value_"]}'


@_register_printer
class STAccount:
    "Pretty printer for ripple::STAccount"
    printer_name = "STAccount"
    version = "1.0"
    type_name_re = "^ripple::STAccount$"

    def __init__(self, value):
        self.value = value
        self.proxy_value = self.value["value_"]
        self.proxy_printer = BaseUInt(self.proxy_value)

    def to_py_value(self):
        return self.proxy_printer.to_py_value()

    def to_string(self):
        return self.proxy_printer.to_string()


@_register_printer
class STBitString:
    "Pretty printer for ripple::STBitString"
    printer_name = "STBitString"
    version = "1.0"
    type_name_re = "^ripple::STBitString<.*>$"

    def __init__(self, value):
        self.value = value
        self.proxy_value = self.value["value_"]
        self.proxy_printer = BaseUInt(self.proxy_value)

    def to_py_value(self):
        return self.proxy_printer.to_py_value()

    def to_string(self):
        return self.proxy_printer.to_string()


@_register_printer
class STObject:
    "Pretty printer for ripple::STObject"
    printer_name = "STObject"
    version = "1.0"
    type_name_re = "^ripple::STObject$"

    def __init__(self, value):
        self.value = value
        self.enabled = True

    def to_py_value(self):
        v = self.value["v_"]
        v_printer = StdVectorPrinter(typename="", val=v)
        r = {}
        for (i, o) in v_printer.children():
            stvar = STVar(o)
            if stvar.is_empty():
                continue
            r[stvar.fname()] = stvar.to_py_value()
        return r

    def to_string(self):
        d = self.to_py_value()
        return json.dumps(d, indent=2)
