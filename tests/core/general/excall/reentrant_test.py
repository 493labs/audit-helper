import sys
sys.path.append('.')
from core.utils.scan_api import get_sli_c
from core.frame.base_node import generate_node
from core.frame.contract_info import ContractInfo
from core.general.nodes.ex_call.reentrant import ReentrantNode
import os
d = os.path.dirname(__file__)

def test_self_reentrant1():
    c = get_sli_c(None,f'{d}/reentrant.sol','reentrant')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(ReentrantNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 1

def test_self_reentrant2():
    c = get_sli_c(None,f'{d}/reentrant.sol','reentrant2')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(ReentrantNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 1

def test_cross_func_reentrant():
    c = get_sli_c(None,f'{d}/reentrant2.sol','SurgeToken')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(ReentrantNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 7 # transfer、transferFrom、purchase， 前两个为误报，还有4个只读的重入风险

def test_only_read_reentrant():
    c = get_sli_c(None,f'{d}/reentrant_only_read.sol','ContractA')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(ReentrantNode, None, False)
    node.check(contract_info)
    assert node.warn_count == 1
