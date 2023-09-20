import sys
sys.path.append('.')
from core.utils.scan_api import get_sli_c
from core.frame.base_node import generate_node
from core.frame.contract_info import ContractInfo
from core.general.nodes.ex_call.unchecked_low_level_call import UncheckedLowLevelCallNode
import os
d = os.path.dirname(__file__)

def test_unchecked_low_level_call():
    c = get_sli_c(None,f'{d}/unchecked_low_level_call.sol','MyConc')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(UncheckedLowLevelCallNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 1