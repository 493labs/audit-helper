import sys
sys.path.append('.')
from core.utils.scan_api import get_sli_c
from core.frame.base_node import generate_node
from core.frame.contract_info import ContractInfo
from core.general.nodes.others.weak_prng import WeakPrng
import os
d = os.path.dirname(__file__)

def test_weak_prng():
    c = get_sli_c(None,f'{d}/weak_prng.sol','Game')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(WeakPrng, None, False)
    node.check(contract_info)
    assert node.warn_count == 1
