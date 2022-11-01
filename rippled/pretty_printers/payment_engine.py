from rippled.pretty_printers.printers import *
from rippled.pretty_printers.printers import _register_printer

import re
import gdb
from libstdcxx.v6.printers import is_specialization_of


@_register_printer
class BoostOptionalStepCache:
    "Pretty Printer for boost::optional Step Cache"
    printer_name = "boost::optional"
    version = "1.0"
    type_name_re = "^boost::optional<ripple::detail(.*)::Cache>$"
    letter_type_name_re = re.compile("^boost::optional<(.*)>$")

    def __init__(self, value):
        self.typename = value.type_name
        self.value = value

    def to_string(self):
        initialized = self.value["m_initialized"]
        if not initialized:
            return "No Cache"
        match = BoostOptionalStepCache.letter_type_name_re.search(self.typename)
        if match:
            try:
                membertype = gdb.lookup_type(match.group(1)).pointer()
                member = self.value["m_storage"]["dummy_"]["data"].address.cast(
                    membertype
                )
                return member.dereference()
            except:
                pass
                return self._iterator("", True)
        return "Error in BoostOptionalStepCache gdb PrettyPrinter"


STEP_DETAIL_NS = ""


@_register_printer
class DirectStepICache:
    "Pretty printer for direct step cache"
    printer_name = "PayDirectStepICache"
    version = "1.0"
    type_name_re = "^ripple::" + STEP_DETAIL_NS + "DirectStepI::Cache$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        return "{src} -> {src_to_dst} -> {dst}".format(
            src=self.value["in"],
            src_to_dst=self.value["srcToDst"],
            dst=self.value["out"],
        )


@_register_printer
class DirectStepI:
    "Pretty printer for direct step"
    printer_name = "PayDirectStepI"
    version = "1.0"
    type_name_re = "^ripple::" + STEP_DETAIL_NS + "DirectStepI$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        return "\n{currency} {src} -> {dst}\n  ({cache})".format(
            currency=self.value["currency_"],
            src=self.value["src_"],
            dst=self.value["dst_"],
            cache=self.value["cache_"],
        )


@_register_printer
class XRPEndpointStep:
    "Pretty printer for xrp endpoint step"
    printer_name = "PayXRPEndpointStep"
    version = "1.0"
    type_name_re = "^ripple::" + STEP_DETAIL_NS + "XRPEndpointStep$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        return "\n(XRPEndpoint) {acc}\n  ({cache})".format(
            acc=self.value["acc_"], cache=self.value["cache_"]
        )


@_register_printer
class Book:
    "Pretty printer for book"
    printer_name = "Book"
    version = "1.0"
    type_name_re = "^ripple::Book$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        return "{src} -> {dst}".format(src=self.value["in"], dst=self.value["out"])


@_register_printer
class BookStepCache:
    "Pretty printer for book step cache"
    printer_name = "PayBookStepCache"
    version = "1.0"
    type_name_re = "^ripple::" + STEP_DETAIL_NS + "BookStep<.*>::Cache$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        return "{src} -> {dst}".format(src=self.value["in"], dst=self.value["out"])


@_register_printer
class BookStep:
    "Pretty printer for book step"
    printer_name = "PayBookStep"
    version = "1.0"
    type_name_re = "^ripple::" + STEP_DETAIL_NS + "BookStep<.*>$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        return "\n{book}\n  ({cache})".format(
            book=self.value["book_"], cache=self.value["cache_"]
        )


@_register_printer
class PayStepUniquePtr:
    "Pretty printer for PayStepUniquePtr"
    printer_name = "PayStepUniquePtr"
    version = "1.0"
    type_name_re = "^std::unique_ptr<ripple::" + STEP_DETAIL_NS + "Step, .*>$"

    def __init__(self, value):
        self.value = value

    def to_string(self):
        impl = None
        try:
            # new implementation
            impl = self.value["_M_t"]["_M_t"]["_M_head_impl"]
        except:
            # old implementation
            impl = self.value["_M_t"]["_M_head_impl"]
        dyn_type = impl.cast(impl.dynamic_type).dereference()
        return f"{dyn_type}"

        # Old implementation of printer - `is_specialization` would not work
        # impl_type = self.value.type.fields()[0].type.tag
        # if is_specialization_of(impl_type, '__uniq_ptr_impl'): # New implementation
        #     impl = self.value['_M_t']['_M_t']['_M_head_impl']
        # elif is_specialization_of(impl_type, 'tuple'):
        #     impl = self.value['_M_t']['_M_head_impl']
        # else:
        #     raise ValueError("Unsupported implementation for unique_ptr: %s" % impl_type)
        # dyn_type = impl.cast(impl.dynamic_type).dereference()
        # return '%s' % dyn_type


@_register_printer
class PayStrand:
    (
        "Pretty printer for pay strand (std::vector<std::unique_ptr<ripple::"
        + STEP_DETAIL_NS
        + "Step>>)"
    )
    printer_name = "PayStrand"
    version = "1.0"
    type_name_re = (
        "^std::vector<std::unique_ptr<ripple::" + STEP_DETAIL_NS + "Step, .*> >$"
    )

    class _iterator:
        def __init__(self, start, finish):
            self.item = start
            self.finish = finish
            self.count = 0

        def __iter__(self):
            return self

        def __next__(self):
            count = self.count
            self.count = self.count + 1
            if self.item == self.finish:
                raise StopIteration
            elt = self.item.dereference()
            self.item = self.item + 1
            return (f"[{count:d}]", elt)

    def __init__(self, value):
        self.value = value

    def children(self):
        return self._iterator(
            self.value["_M_impl"]["_M_start"], self.value["_M_impl"]["_M_finish"]
        )

    def display_hint(self):
        return "array"

    def to_string(self):
        start = self.value["_M_impl"]["_M_start"]
        finish = self.value["_M_impl"]["_M_finish"]
        size = int(finish - start)
        if size == 0:
            return "Paystrand (empty)"
        return f"Paystrand ({size:d})"
