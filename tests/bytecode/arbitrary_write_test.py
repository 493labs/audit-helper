import sys
sys.path.append('.')
from bytecode.util.solidity import get_contract
from bytecode.analyze.arbitrary_write import arbitrary_write_check

def test_arbitrary_write():
    solidity_contract = get_contract(None, './tests/examples/arbitrary_write.sol','ArbitraryWrite')
    assert arbitrary_write_check(solidity_contract.disassembly) == True

def test_no_arbitrary_write():
    solidity_contract = get_contract(None, './tests/examples/arbitrary_write.sol','NoArbitraryWrite')
    assert arbitrary_write_check(solidity_contract.disassembly) == False