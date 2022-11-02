# GDB utilities for rippled

This is an scripts to improve debugging the [XRP Ledger](https://xrpl.org) in
gdb on linux. It requires python 3.10 or better.

I built these for my own use, but I hope other XRP Ledger developers find these
useful. I welcome improvements.

## Key Features

The primary feature is a set of pretty printers. There are printers for:

* STAmount
* IOUAmount
* XRPAmount
* Issue
* Buffer
* STObject (and derived classes)
* STBitString
* STAccount
* STInteger
* STBase
* STVar
* SField
* BaseUInt (including special printers for AccountID and Currency)
* JsonValue

There is also special support known accounts - this is useful when debugging
unit tests and when replaying transactions. For example, in unit tests, the
account "rG1QQv2nh2gr7RCZ1P8YYcBUKCCN633jCn" is always "alice". The pretty
printer will display "alice" when it sees that account (or any of the other
well-known accounts).

As an example for what these scripts do, here's an example of how gdb would display a ledger object without the pretty printer:

```gdb 
  members of ripple::STObject:
    v_ = {
      <std::_Vector_base<ripple::detail::STVar, std::allocator<ripple::detail::STVar> >> = {
        _M_impl = {
          <std::allocator<ripple::detail::STVar>> = {
            <std::__new_allocator<ripple::detail::STVar>> = {<No data fields>}, <No data fields>}, 
          <std::_Vector_base<ripple::detail::STVar, std::allocator<ripple::detail::STVar> >::_Vector_impl_data> = {
            _M_start = 0x7fffdc04c3b0,
            _M_finish = 0x7fffdc04cbf0,
            _M_end_of_storage = 0x7fffdc04cbf0
          }, <No data fields>}
      }, <No data fields>},
    mType = 0x555562f77428
  }, 
  <ripple::CountedObject<ripple::STLedgerEntry>> = {<No data fields>}, 
  members of ripple::STLedgerEntry:
  key_ = {
    data_ = {
      _M_elems = {851601963, 3830140074, 614331419, 55245401, 1135993159, 3459238308, 35422944, 2833900033}
    }
  },
  type_ = ripple::ltACCOUNT_ROOT
```

Here's the same ledger object with the pretty printer (notice the "Account" is
"master", not "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh", since this is a well-known
account):

```gdb
$13 = (std::__shared_ptr_access<ripple::STLedgerEntry, (__gnu_cxx::_Lock_policy)2, false, false>::element_type &) @0x7fffdc0880f0: {
  <ripple::STObject> = {
  "Account": "master",
  "Sequence": 3,
  "Balance": "99999989999.999970/XRP/RootAccount",
  "OwnerCount": 0,
  "PreviousTxnID": "(ripple::base_uint<256, void>) 3077E7D79E2814543A19322FADC2E4B21FD90846B1C1F5D0B736094FCFE40557",
  "PreviousTxnLgrSeq": 3,
  "LedgerEntryType": 97,
  "Flags": 0
}, 
  <ripple::CountedObject<ripple::STLedgerEntry>> = {<No data fields>}, 
  members of ripple::STLedgerEntry:
  key_ = (ripple::base_uint<256, void>) 2B6AC232AA4C4BE41BF49D2459FA4A0347E1B543A4C92FCEE0821C0201E2E9A8,
  type_ = ripple::ltACCOUNT_ROOT
}
```

## Installation

In the `.gdbinit` files, add a section for python, and make sure the gdb pretty
printers are on the sys path, and then add the directory where this project
lives to the path. For example:

``` gdb
python

import platform
import os
import sys
from os.path import expanduser

home = expanduser('~')

if os.path.isdir('/usr/share/gcc-12.2.0/python'):
    sys.path.insert(0, '/usr/share/gcc-12.2.0/python')
    from libstdcxx.v6.printers import register_libstdcxx_printers
    register_libstdcxx_printers (None)

sys.path.insert(0, home + '/apps/gdb_python')
from rippled.pretty_printers.printers import register_rippled_printers
register_rippled_printers(None)

end
```

Of course, replace home + '/apps/gdb_python' with the location of this project
and `/usr/share/gcc-12.2.0/python` with the location of the gcc pretty printers
on your system.
