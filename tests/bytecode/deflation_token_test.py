import sys
sys.path.append('.')
from bytecode.util import get_contract
from bytecode.strategy.deflation_token_check import deflation_token_check2

from mythril.laser.ethereum.time_handler import time_handler

def test_fee_token():
    solidity_contract = get_contract(None, './tests/examples/token_fee.sol','FeeToken')
    time_handler.start_execution(10)
    assert deflation_token_check2(solidity_contract.code) == True

def test_nofee_token():
    solidity_contract = get_contract(None, './tests/examples/token_fee.sol','NoFeeToken')
    time_handler.start_execution(10)
    assert deflation_token_check2(solidity_contract.code) == False

def test_complex_token():
    solidity_contract = get_contract(None, './tests/examples/KishuInu.sol','KishuInu')
    time_handler.start_execution(10)
    assert deflation_token_check2(solidity_contract.code) == True
