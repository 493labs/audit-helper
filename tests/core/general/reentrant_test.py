import sys
sys.path.append('.')
from core.utils.scan_api import get_sli_c
from core.frame.base_node import generate_node
from core.frame.contract_info import ContractInfo
from core.general.nodes.external_call import ReentrantNode

def test_dangerous_excall1():
    c = get_sli_c(None,'./tests/core/example/reentrant.sol','reentrant')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(ReentrantNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 1

def test_dangerous_excall2():
    c = get_sli_c(None,'./tests/core/example/reentrant.sol','reentrant2')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(ReentrantNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 1

def test_dangerous_excall3():
    c = get_sli_c(None,'./tests/core/example/reentrant2.sol','SurgeToken')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(ReentrantNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 3 # transfer、transferFrom、purchase， 前两个为误报
