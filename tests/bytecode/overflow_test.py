import sys
sys.path.append('.')
from bytecode.util.solidity import get_contract
from bytecode.analyze.overflow import overflow_check

def test_overflow_check():
    solidity_contract = get_contract(None, './tests/examples/overflow.sol','Overflow')
    assert overflow_check(solidity_contract.disassembly) == True

def test_no_overflow_check():
    solidity_contract = get_contract(None, './tests/examples/overflow.sol','NoOverflow')
    assert overflow_check(solidity_contract.disassembly) == False
