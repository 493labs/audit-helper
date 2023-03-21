import sys
sys.path.append('.')
from bytecode.util import get_contract
from bytecode.analyze.delegate_call import arbitrary_delegate_call

def test_delegate_call_simple():
    solidity_contract = get_contract(None, './tests/examples/delegate_call.sol','DelegateCallSimple')
    assert arbitrary_delegate_call(solidity_contract.disassembly) == True

def test_no_delegate_call():
    solidity_contract = get_contract(None, './tests/examples/delegate_call.sol','DelegateCall')
    assert arbitrary_delegate_call(solidity_contract.disassembly) == False

def test_delegate_call():
    solidity_contract = get_contract(None, './tests/examples/delegate_call.sol','DelegateCall')
    assert arbitrary_delegate_call(solidity_contract.disassembly, 2) == True

