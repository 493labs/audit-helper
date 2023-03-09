import sys
sys.path.append('.')
from bytecode.util import get_contract
from bytecode.strategy.loop_check import loop_check, loop_check_with_concrete_storage

from mythril.laser.ethereum.time_handler import time_handler

def test_loop_check():
    solidity_contract = get_contract(None, './tests/examples/loop.sol','Loop')
    time_handler.start_execution(10)
    assert loop_check(solidity_contract.creation_code) == True

def test_noloop_check():
    solidity_contract = get_contract(None, './tests/examples/loop.sol','NoLoop')
    time_handler.start_execution(10)
    assert loop_check(solidity_contract.creation_code) == False

def test_complex_loop_check():
    solidity_contract = get_contract(None,'./tests/examples/KishuInu.sol','KishuInu')
    time_handler.start_execution(100)
    assert loop_check_with_concrete_storage(solidity_contract.code) == True