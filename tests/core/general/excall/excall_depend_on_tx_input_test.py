import sys
sys.path.append('.')
from core.utils.scan_api import get_sli_c
from core.frame.base_node import generate_node
from core.frame.contract_info import ContractInfo
from core.general.nodes.ex_call.excall_depend_on_tx_input import ExCallDependOnTxInputNode
import os
d = os.path.dirname(__file__)

def test_dangerous_excall1():
    c = get_sli_c(None,f'{d}/ex_call.sol','OutCall1')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(ExCallDependOnTxInputNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 2

def test_dangerous_excall2():
    c = get_sli_c(None,f'{d}/ex_call.sol','OutCall2')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(ExCallDependOnTxInputNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 2
