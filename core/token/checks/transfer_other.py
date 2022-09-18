from typing import List, Mapping, Tuple
from slither.core.declarations import Contract, Function, SolidityFunction
from slither.core.variables.state_variable import StateVariable
from slither.core.cfg.node import Node, NodeType

def get_dominance_frontier(node: Node)-> Node:
    if node.type == NodeType.IFLOOP:
        # 循环时的边界指向了循环
        return node.son_false.sons[0]
    elif node.type == NodeType.IF:
        return list(node.dominance_frontier)[0]

def if_dominance_read_state(if_node:Node, state:StateVariable)-> bool:
    assert if_node.type == NodeType.IF, f'if_dominance_read_state 的参数需要为if节点：{if_node.expression}'
    if if_node.son_true:
        is_read, contain_return = branch_read_state(if_node.son_true, state)
        if not is_read :
            return False, contain_return
    if if_node.son_false:
        is_read, contain_return = branch_read_state(if_node.son_false, state)
        if not is_read :
            return False, contain_return
    return True, contain_return

def branch_read_state(node:Node, state:StateVariable)->Tuple[bool,bool]:
    is_read = False
    contain_return = False
    while True:
        if state in node.state_variables_read:
            is_read = True
            break
        for internal_call in node.internal_calls:
            if not isinstance(internal_call, SolidityFunction):
                if branch_read_state(internal_call.entry_point,state)[0]:
                    is_read = True
                    break

        if node.type == NodeType.RETURN:
            contain_return = True
            break

        if node.type == NodeType.IF:
            is_read, contain_return = if_dominance_read_state(node, state)
            if not is_read and contain_return:
                break
            else:
                node = get_dominance_frontier(node)
                continue 

        if node.type == NodeType.IFLOOP:  
            # 暂不考虑循环的细节处理 
            node = get_dominance_frontier(node)
            continue      

        
        if len(node.sons) == 0:
            break
        if node.immediate_dominator in node.sons:
            break        
        # assert len(node.sons) == 1, f'len(node.sons) != 1'
        node = node.sons[0]
    return (is_read, contain_return)



def func_read_state_in_all_paths(transferFrom_func: Function, approval_state: StateVariable) -> bool:
    # transferFrom_func.nodes_ordered_dominators
    return branch_read_state(transferFrom_func.entry_point, approval_state)[0]

def transfer_from_without_approval2(transferFrom_func: Function, approval_state: StateVariable)-> bool:
    entry_point = transferFrom_func.entry_point
    cur_nodes: List[Node] = []
    fork_stack: List[Node] = []
    cur_nodes.append(entry_point)
    fork_stack.append(entry_point.sons[0])
    while len(fork_stack) > 0:
        fork_node = fork_stack.pop()
        # 循环时会怎么样？
        last_node_index = cur_nodes.index(fork_node.fathers[0])
        cur_nodes = cur_nodes[:last_node_index + 1]        
        cur_nodes.append(fork_node)        
        any_path_without_approval = False
        while True:            
            cur_node = cur_nodes[-1]
            if len(cur_node.sons) == 0 or isinstance(cur_node, NodeType.RETURN):
                # 路径终点
                all_node_without_approval = True
                for node in cur_nodes:
                    if approval_state in node.state_variables_read:
                        all_node_without_approval = False
                        break
                    if any(
                        not isinstance(internal_call,SolidityFunction)  and not transfer_from_without_approval2(internal_call)
                        for internal_call in node.internal_calls
                    ):
                        # 任一调用中含有approval读取（意味着若该调用中含有分支，则需要所有分支都对approval进行读取）
                        all_node_without_approval = False
                        break
                if all_node_without_approval:
                    any_path_without_approval = True
                    break
            if isinstance(cur_node, NodeType.IF):
                # 分叉节点
                pass
                
        if any_path_without_approval:
            return True
    return False
        # if any(
        #     c.name in ["revert()", "revert(string)", "revert"] for c in cur_node.internal_calls
        # ):
        #     if len(fork_stack) == 0:
        #         break
        #     else:
        #         continue
