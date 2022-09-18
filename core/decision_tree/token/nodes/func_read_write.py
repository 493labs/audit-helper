from typing import List
from ..common.base_node import DecisionNode, NodeReturn
from ..common.standard import ERC20_E_view, TokenInfo, ERC20_E_Require

from slither.core.declarations import  Function, SolidityVariableComposed
from slither.core.variables.state_variable import StateVariable

def func_only_op_state(f: Function, is_write:bool, states_required: List[StateVariable]):
    '''
    判断某方法是否只读取或写入了指定的states
    '''
    states = f.all_state_variables_written() if is_write else f.all_state_variables_read()

    ret:List[str] = []
    for state in states:
        if state not in states_required:
            ret.append(f" {f.name} 对 {state.name} 有意料之外的{'写入' if is_write else '读取'}")
    for state in states_required:
        if state not in states:
            ret.append(f" {f.name} 对 {state.name} 没有应该有的{'写入' if is_write else '读取'}")
    return ret

WRITE_FLAG = True
READ_FLAG = False

class RequiredFuncNode(DecisionNode):
    def check(self, token_info: TokenInfo) -> NodeReturn:
        msg_sender = SolidityVariableComposed("msg.sender")
        for e in ERC20_E_Require._member_map_.values():
            if msg_sender not in token_info.get_f(e).all_solidity_variables_read():
                self.layerouts.append(f'{e.value}未读取msg.sender') 
        checks = [
            (ERC20_E_Require.transfer, [ERC20_E_view.balanceOf], [ERC20_E_view.balanceOf]),
            (ERC20_E_Require.approve, [], [ERC20_E_view.allowance]),
            (ERC20_E_Require.transferFrom, [ERC20_E_view.balanceOf,ERC20_E_view.allowance], [ERC20_E_view.balanceOf,ERC20_E_view.allowance])
        ]
        for check in checks:
            f = token_info.get_f(check[0])
            states_read = [token_info.state_map[e] for e in check[1]]
            states_write = [token_info.state_map[e] for e in check[2]]
            self.layerouts.extend(func_only_op_state(f, READ_FLAG, states_read))
            self.layerouts.extend(func_only_op_state(f, WRITE_FLAG, states_write))
        if len(self.layerouts) == 0:
            self.layerouts.append('标准方法读写集检查无异常')
            self.layerouts.append('检查完毕，标准的erc20代币')
            return NodeReturn.reach_leaf
        else:
            self.layerouts.append('暂未对读写集异常情况进行分析')
            return NodeReturn.reach_leaf