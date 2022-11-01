from rippled.pretty_printers.printers import *
from rippled.pretty_printers.printers import _register_printer

import re
import json
from libstdcxx.v6.printers import StdMapPrinter


@_register_printer
class JsonValueCZString:
    "Pretty printer for Json::Value::CZString"
    printer_name = "JsonValueCZString"
    version = "1.0"
    type_name_re = "^Json::Value::CZString$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        return self.value["cstr_"]


@_register_printer
class JsonValue:
    "Pretty printer for Json::Value"
    printer_name = "JsonValue"
    version = "1.0"
    type_name_re = "^Json::Value$"

    nullValue = 0
    intValue = 1
    uintValue = 2
    realValue = 3
    stringValue = 4
    booleanValue = 5
    arrayValue = 6
    objectValue = 7

    def __init__(self, value):
        self.value = value

    def to_py_value(self):
        value_type = self.value["type_"]
        match value_type:
            case JsonValue.nullValue:
                return None
            case JsonValue.intValue:
                return int(self.value["value_"]["int_"])
            case JsonValue.uintValue:
                return int(self.value["value_"]["uint_"])
            case JsonValue.realValue:
                return float(self.value["value_"]["real_"])
            case JsonValue.stringValue:
                return self.value["value_"]["string_"].string()
            case JsonValue.booleanValue:
                return bool(self.value["value_"]["bool_"])
            case JsonValue.objectValue:
                m = self.value["value_"]["map_"].dereference()
                map_printer = StdMapPrinter(typename="", val=m)
                k = None
                d = {}
                for (i, (_, v)) in enumerate(map_printer.children()):
                    if not i % 2:
                        k = v["cstr_"].string()
                    else:
                        d[k] = JsonValue(v).to_py_value()
                return d
            case JsonValue.arrayValue:
                return self.value["value_"]["map_"].dereference()

    def to_string(self):
        d = self.to_py_value()
        return json.dumps(d, indent=2)
