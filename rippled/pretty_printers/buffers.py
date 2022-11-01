from rippled.pretty_printers.printers import *
from rippled.pretty_printers.printers import _register_printer

import re


@_register_printer
class Buffer:
    "Pretty printer for Buffer"
    printer_name = "Buffer"
    version = "1.0"
    type_name_re = "^ripple::Buffer$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        vals = []
        array = self.value["p_"]["_M_t"]["_M_head_impl"]
        for i in range(int(self.value["size_"])):
            if i > 0 and not (i % 16):
                vals.append("\n ")
            vals.append(f"{int(array[i]):.2x}")
        vals = " ".join(vals)
        return "(Buffer: %s)\n{ %s }" % (self.value["size_"], vals)
