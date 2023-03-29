import sys
sys.path.append('.')
from bytecode.util.solidity import get_contract
from bytecode.analyze.is_contract_check import is_contract_check

def test_arbitrary_write():
    solidity_contract = get_contract(None, './tests/examples/is_contract.sol','Address')
    assert is_contract_check(solidity_contract.disassembly) == True