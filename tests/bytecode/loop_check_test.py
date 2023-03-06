import sys
sys.path.append('.')
from bytecode.util import get_contract
from bytecode.strategy.base import loop_check

def test_loop_check():
    solidity_contract = get_contract(None, './tests/examples/loop.sol','Loop')
    assert loop_check(solidity_contract.creation_code) == True

def test_noloop_check():
    solidity_contract = get_contract(None, './tests/examples/loop.sol','NoLoop')
    assert loop_check(solidity_contract.creation_code) == False
