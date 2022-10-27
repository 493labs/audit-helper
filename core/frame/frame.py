from typing import List, Mapping

from .contract_info import ContractInfo
from .base_node import DecisionNode, generate_node, NodeReturn

def make_decision(
        decision_tree: Mapping[DecisionNode, List[DecisionNode]],
        start_node: type[DecisionNode],
        contract_info: ContractInfo,
        on_chain: bool=False    
    ):    

    cur_node = generate_node(start_node, None, on_chain)
    while True:
        ret = cur_node.check(contract_info)
        if ret == NodeReturn.reach_leaf:
            break                    
        if cur_node.__class__ not in decision_tree:
            break
        next_node = decision_tree[cur_node.__class__][ret.value]
        cur_node = generate_node(next_node, cur_node, on_chain)

    return cur_node.output()