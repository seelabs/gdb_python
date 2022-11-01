from rippled.pretty_printers.printers import *
from rippled.pretty_printers.printers import _register_printer

from . import known_accounts

import re
import gdb
import binascii
import re
import base64
from hashlib import sha256

from gdb.types import get_basic_type

ALPHABET = b"rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz"


def base58_encode(n):
    l = []
    while n > 0:
        n, r = divmod(n, 58)
        l.append(ALPHABET[r])
    return bytes(reversed(l))


def base58_encode_padded(s):
    n = int(base64.b16encode(s), 16)
    res = base58_encode(n)
    pad = 0
    for c in s:
        if c == 0:
            pad += 1
        else:
            break
    return bytes([ALPHABET[0]] * pad) + res


def checksum(b):
    """Returns a 4-byte checksum of a binary."""
    return sha256(sha256(b).digest()).digest()[:4]


def encode(b, version):
    vs = bytes((version,)) + b
    check = checksum(vs)
    return str(base58_encode_padded(vs + check), "ascii")


@_register_printer
class BaseUInt:
    "Pretty Printer for ripple::base_uint<Bits, Tab>"
    printer_name = "ripple::base_uint"
    version = "1.0"
    type_name_re = "^ripple::base_uint.*$"
    type_fields_re = re.compile(r"^ripple::base_uint<(\d+)[^,]*,\s*([^>]*)>$")
    known_accounts = known_accounts.known_accounts

    def __init__(self, value):
        self.value = value
        self.num_bits = None
        self.tag_name = None
        self.basic_type = get_basic_type(self.value.type)
        self.type_name = str(self.basic_type)
        res = BaseUInt.type_fields_re.match(self.type_name)
        if res:
            fields = res.groups()
        if fields:
            self.num_bits = int(fields[0])
            self.tag_name = fields[1]
            if self.tag_name.endswith("Tag"):
                self.tag_name = self.tag_name[:-3]
            sw = "ripple::detail::"
            if self.tag_name.startswith(sw):
                self.tag_name = self.tag_name[len(sw) :]

    def to_py_value(self):
        return self.to_string()

    def to_string(self):
        pn = self.value["data_"]
        if self.num_bits is not None and self.tag_name is not None:
            num_bytes = self.num_bits // 8
            mem = bytes(gdb.selected_inferior().read_memory(pn.address, num_bytes))
            if self.tag_name == "AccountID":
                if not any(mem):
                    return "RootAccount"
                version = 0
                encoded = encode(mem, version)
                if encoded in BaseUInt.known_accounts:
                    return BaseUInt.known_accounts[encoded]
                return f"({self.tag_name}) {encoded}"
            if self.tag_name == "Currency":
                if not any(mem[0:12]) and not any(mem[16:]):
                    if not any(mem[12:15]):
                        return "XRP"
                    return str(mem[12:15], "ascii")
                return f"({self.tag_name}) {pn}"
        return f"({self.type_name}) {binascii.hexlify(mem).upper().decode('utf-8')}"
