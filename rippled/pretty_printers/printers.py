# encoding: utf-8

# Pretty-printers for rippled
# Requires python 3.10 or later
#
# Inspired _but not copied_ from boost and libstdc++'s pretty printers
#


import gdb
import gdb.printing
import re

from gdb.types import get_basic_type


class GDB_Value_Wrapper(gdb.Value):
    "Wrapper class for gdb.Value that allows setting extra properties."

    def __init__(self, value):
        super().__init__(value)
        self.__dict__ = {}


class Printer_Gen:
    class SubPrinter_Gen:
        def match_re(self, v):
            return self.re.search(str(v.basic_type)) != None

        def __init__(self, Printer):
            self.name = f"{Printer.printer_name}-{Printer.version}"
            self.enabled = True
            if hasattr(Printer, "supports"):
                self.re = None
                self.supports = Printer.supports
            else:
                self.re = re.compile(Printer.type_name_re)
                self.supports = self.match_re
            self.Printer = Printer

        def __call__(self, v):
            if not self.enabled:
                return None
            if self.supports(v):
                v.type_name = str(v.basic_type)
                return self.Printer(v)
            return None

    def __init__(self, name):
        self.name = name
        self.enabled = True
        self.subprinters = []

    def add(self, Printer):
        self.subprinters.append(Printer_Gen.SubPrinter_Gen(Printer))

    def __call__(self, value):
        v = GDB_Value_Wrapper(value)
        v.basic_type = get_basic_type(v.type)
        if not v.basic_type:
            return None
        for subprinter_gen in self.subprinters:
            printer = subprinter_gen(v)
            if printer != None:
                return printer
        return None


printer_gen = Printer_Gen("rippled")


# This function registers the top-level Printer generator with gdb.
# This should be called from .gdbinit.
def register_rippled_printers(obj):
    "Register printer generator with objfile obj."
    from . import amounts
    from . import base_uint
    from . import buffers
    from . import json_value
    from . import payment_engine
    from . import stobject

    global printer_gen
    gdb.printing.register_pretty_printer(obj, printer_gen, replace=True)


# Register individual Printer with the top-level Printer generator.
def _register_printer(Printer):
    "Registers a Printer"
    global printer_gen
    printer_gen.add(Printer)
    return Printer


###
### Individual Printers follow.
###
### Relevant fields:
###
### - 'printer_name' : Subprinter name used by gdb. (Required.) If it contains
###     regex operators, they must be escaped when refering to it from gdb.
### - 'version' : Appended to the subprinter name. (Required.)
### - 'supports(GDB_Value_Wrapper)' classmethod : If it exists, it is used to
###     determine if the Printer supports the given object.
### - 'type_name_re' : If 'supports(basic_type)' doesn't exist, a default
###     version is used which simply tests whether the type name matches this
###     re. (Either supports() or type_name_re is required.)
### - '__init__' : Its only argument is a GDB_Value_Wrapper.
###


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
