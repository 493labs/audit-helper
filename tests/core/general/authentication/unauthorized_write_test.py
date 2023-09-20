import sys
sys.path.append('.')
from core.utils.scan_api import get_sli_c
from core.frame.base_node import generate_node
from core.frame.contract_info import ContractInfo
from core.general.nodes.authentication.unauthorized_write import UnauthorizedWriteNode
import os
d = os.path.dirname(__file__)

def test_UnusualAuthenticate1():
    c = get_sli_c(None,d + '/authenticate.sol','UnusualAuthenticate1')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(UnauthorizedWriteNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 1

def test_UnusualAuthenticate2():
    c = get_sli_c(None,d + '/authenticate.sol','UnusualAuthenticate2')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(UnauthorizedWriteNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 0