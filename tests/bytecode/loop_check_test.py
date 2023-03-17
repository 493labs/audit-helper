import sys
sys.path.append('.')
from bytecode.util import get_contract
from bytecode.frame.svm import SVM

def test_loop_check():
    solidity_contract = get_contract(None, './tests/examples/loop.sol','Loop')
    svm = SVM()
    assert svm.loop_check(solidity_contract.disassembly) == True

def test_noloop_check():
    solidity_contract = get_contract(None, './tests/examples/loop.sol','NoLoop')
    svm = SVM()
    assert svm.loop_check(solidity_contract.disassembly) == False

def test_complex_loop_check():
    solidity_contract = get_contract(None,'./tests/examples/KishuInu.sol','KishuInu')
    svm = SVM()
    assert svm.loop_check(solidity_contract.disassembly) == True
    