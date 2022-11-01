import gdb
from gdb.types import get_basic_type
import binascii
import collections
import pickle
import decimal
import os
from collections import namedtuple
from os.path import expanduser
from rippled.printers import XRPAmount, IOUAmount, STAmount
import re

DEFAULT_OUTPUT_DIR = expanduser('~/py_data_gdb/')


def _to_decimal(sign, value, exponent):
    # Decimal want a tuple of digits, use this ugly hack
    # until I think of a better way
    value_tuple = tuple(int(d) for d in tuple('%d' % value))
    return decimal.Decimal((sign, value_tuple, exponent))


def _st_amt_to_decimal(value):
    sign = int(value['mIsNegative'])
    mantissa = int(value['mValue'])
    exponent = -6 if int(value['mIsNative']) else int(value['mOffset'])
    return _to_decimal(sign, mantissa, exponent)


def _xrp_amt_to_decimal(value):
    drops = int(value['drops_'])
    sign = 0
    if drops < 0:
        drops = -drops
        sign = 1
    exponent = -6
    return _to_decimal(sign, drops, exponent)


def _iou_amt_to_decimal(value):
    mantissa = int(value['mantissa_'])
    sign = 0
    if mantissa < 0:
        mantissa = -mantissa
        sign = 1
    exponent = int(value['exponent_'])
    return _to_decimal(sign, mantissa, exponent)


XRP_AMT_RE = re.compile(XRPAmount.type_name_re)
IOU_AMT_RE = re.compile(IOUAmount.type_name_re)
ST_AMT_RE = re.compile(STAmount.type_name_re)


def _amt_to_decimal(value):
    bt = get_basic_type(value.type)
    if XRP_AMT_RE.match(bt.name):
        return _xrp_amt_to_decimal(value)
    if IOU_AMT_RE.match(bt.name):
        return _iou_amt_to_decimal(value)
    if ST_AMT_RE.match(bt.name):
        return _st_amt_to_decimal(value)
    return None


def _txid_to_hex_str(txid):
    pn = txid['pn']
    num_bytes = 32
    mem = bytes(gdb.selected_inferior().read_memory(pn.address, num_bytes))
    return binascii.hexlify(mem).upper().decode('utf-8')


def _value(sym_name):
    f = gdb.selected_frame()
    s = gdb.lookup_symbol(sym_name)[0]
    return s.value(f)


def _txid():
    v = _value('this')
    tid = v['ctx_']['tx']['tid_']
    return tid

# dict so we can pickle and load without depending on the rippled namespace
TX_FLOW = {}


def tx_flow_init(txid):
    return {'txid': txid, 'in': [], 'out': [], 'iter': []}


def tx_flow_append(tx_flow, input, output, it):
    tx_flow['in'].append(input)
    tx_flow['out'].append(output)
    tx_flow['iter'].append(it)


TX_FLOW = None
LAST_TX_FLOW = None  # for inspecting directly


def save_tx_flow(out_dir=DEFAULT_OUTPUT_DIR):
    '''Pickle the collected traces. File name will contain the tx id'''
    global TX_FLOW
    if not TX_FLOW:
        return
    file_name = os.path.join(out_dir,
                             'tx.' + TX_FLOW['new']['txid'] + '.pickle')
    with open(file_name, 'wb') as f:
        pickle.dump(TX_FLOW, f)


class BPaymentTxStart(gdb.Breakpoint):
    '''Start of payment transaction'''

    def __init__(self, spec=None):
        if spec is None:
            spec = 'Payment.cpp:361'
        super().__init__(spec)

    def stop(self):
        global TX_FLOW
        if TX_FLOW:
            return TRUE  # TDB - this is an error
        tid_hex = _txid_to_hex_str(_txid())
        TX_FLOW = {'old': tx_flow_init(tid_hex), 'new': tx_flow_init(tid_hex)}
        return False  # Don't actually break


class BPaymentTxFinish(gdb.Breakpoint):
    '''End of payment transaction'''

    def __init__(self, spec=None):
        if spec is None:
            spec = 'Payment.cpp:374'
        super().__init__(spec)

    def stop(self):
        global TX_FLOW, LAST_TX_FLOW
        if not TX_FLOW:
            return True  # TDB - this is an error
        LAST_TX_FLOW = TX_FLOW
        TX_FLOW = None
        return True  # Don't actually break


class BNewFlowStrandCand(gdb.Breakpoint):
    '''Candidate liquidity new flow'''

    def __init__(self, spec=None):
        if spec is None:
            spec = 'impl/Flow.h:381'
        super().__init__(spec)

    def stop(self):
        global TX_FLOW
        if not TX_FLOW:
            return True  # TDB - this is an error
        v = _value('f')
        vin = _amt_to_decimal(v['in'])
        vout = _amt_to_decimal(v['out'])
        cur_try = int(_value('curTry'))
        tx_flow_append(TX_FLOW['new'], vin, vout, cur_try - 1)
        return False  # Don't actually break


class BOldFlowStrandCand(gdb.Breakpoint):
    '''Candidate liquidity old flow'''

    def __init__(self, spec=None):
        if spec is None:
            spec = 'RippleCalc.cpp:369'
        super().__init__(spec)

    def stop(self):
        global TX_FLOW
        if not TX_FLOW:
            return True  # TDB - this is an error
        v = _value('pathState')['_M_ptr'].dereference()
        vin = _amt_to_decimal(v['saInPass'])
        vout = _amt_to_decimal(v['saOutPass'])
        cur_try = int(_value('iPass'))
        tx_flow_append(TX_FLOW['old'], vin, vout, cur_try)
        return False  # Don't actually break


class BCmpNewOldFlow(gdb.Breakpoint):
    '''Old and new results disagree'''

    def __init__(self, spec=None):
        if spec is None:
            spec = 'RippleCalc.cpp:164'
        super().__init__(spec)

    def stop(self):
        save_tx_flow()
        return True  # Don't actually break
