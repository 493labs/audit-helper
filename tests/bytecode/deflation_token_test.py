import sys
sys.path.append('.')
from bytecode.util.solidity import get_contract

from bytecode.analyze.deflation_token import deflation_token_check

def test_fee_token():
    solidity_contract = get_contract(None, './tests/bytecode/examples/token_fee.sol','FeeToken')
    assert deflation_token_check(solidity_contract.disassembly) == True

def test_nofee_token():
    solidity_contract = get_contract(None, './tests/bytecode/examples/token_fee.sol','NoFeeToken')
    assert deflation_token_check(solidity_contract.disassembly) == False

def test_complex_token():
    solidity_contract = get_contract(None, './tests/bytecode/examples/KishuInu.sol','KishuInu')
    assert deflation_token_check(solidity_contract.disassembly) == True
