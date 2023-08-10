from typing import List, Mapping
from slither.core.declarations import Contract
from eth_typing.evm import ChecksumAddress

from core.utils.url import Chain
from core.utils.scan_api import get_sli_c_by_addr
from core.frame.frame import make_decision

from core.frame.contract_info import ContractInfo
from .base_node import ContractDecisionNode
from .tree_config import contract_decision_tree, ContractUpgradeNode  

def contract_decision(        
        on_chain: bool=False, 
        chain: Chain=None, 
        address: ChecksumAddress = None, 
        c: Contract=None,
        decision_tree: Mapping[ContractDecisionNode, List[ContractDecisionNode]] = contract_decision_tree,
        start_node: type[ContractDecisionNode] = ContractUpgradeNode  
    ):
    contract_info = ContractInfo()
    contract_info.chain = chain
    contract_info.address = address
    if c == None:
        c = get_sli_c_by_addr(chain, address)
    contract_info.c = c

    return make_decision(decision_tree, start_node, contract_info, on_chain)
