import sys
sys.path.append('.')
from bytecode.util import get_contract
from bytecode.analyze.arbitrary_write import arbitrary_write_check

from mythril.laser.ethereum.time_handler import time_handler

def test_arbitrary_write_check():
    solidity_contract = get_contract(None, './tests/examples/merde.sol','Merde')
    time_handler.start_execution(60)
    assert arbitrary_write_check(solidity_contract.creation_code) == True

# test_arbitrary_write_check()