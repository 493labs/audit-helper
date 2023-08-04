import sys
sys.path.append('.')
from core.utils.scan_api import get_sli_c
from core.frame.base_node import generate_node
from core.frame.contract_info import ContractInfo
from core.general.nodes.dangerous_opcode import DangerousOpcodeNode

def test_delegatecall():
    c = get_sli_c(None,'./tests/core/example/delegatecall.sol','Router')
    contract_info = ContractInfo()
    contract_info.c = c
    node = generate_node(DangerousOpcodeNode, None, False)
    node.check(contract_info)
    assert node.warn_count > 0