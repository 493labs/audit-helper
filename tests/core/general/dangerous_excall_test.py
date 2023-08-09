import sys
sys.path.append('.')
from core.utils.scan_api import get_sli_c
from core.frame.base_node import generate_node
from core.frame.contract_info import ContractInfo
from core.general.nodes.external_call import DangerousExCallNode

def test_dangerous_excall1():
    c = get_sli_c(None,'./tests/core/example/ex_call.sol','OutCall1')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(DangerousExCallNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 2

def test_dangerous_excall2():
    c = get_sli_c(None,'./tests/core/example/ex_call.sol','OutCall2')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(DangerousExCallNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 2
