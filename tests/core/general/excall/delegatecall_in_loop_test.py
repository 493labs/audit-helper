import sys
sys.path.append('.')
from core.utils.scan_api import get_sli_c
from core.frame.base_node import generate_node
from core.frame.contract_info import ContractInfo
from core.general.nodes.ex_call.delegatecall_in_loop import DelegatecallInLoopNode
import os
d = os.path.dirname(__file__)

def test_delegatecall_in_loop():
    c = get_sli_c(None,f'{d}/delegatecall_in_loop.sol','DelegatecallInLoop')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(DelegatecallInLoopNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 1