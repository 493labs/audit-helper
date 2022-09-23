from enum import Enum
from typing import List, Tuple
from ..common.base_node import DecisionNode, NodeReturn
from ..common.token import ERC20_E_view, TokenInfo, ERC20_E_Require, ERC721_E_Require, ERC721_E_view

from slither.core.declarations import  Function, SolidityVariableComposed
from slither.core.variables.state_variable import StateVariable

def func_only_op_state(f: Function, is_write:bool, states_required: List[StateVariable]):
    '''
    判断某方法是否只读取或写入了指定的states
    '''
    states = f.all_state_variables_written() if is_write else f.all_state_variables_read()
    
    surplus_states:List[StateVariable] = []
    scarcity_states:List[StateVariable] = []
    for state in states:
        if state not in states_required:
            surplus_states.append(state)
    for state in states_required:
        if state not in states:
            scarcity_states.append(state)
    
    ret:List[str] = []
    names = ','.join([state.name for state in surplus_states])
    if names:
        ret.append(f"{f.full_name} 对 {names} 有意料之外的{'写入' if is_write else '读取'}")
    names = ','.join([state.name for state in scarcity_states])
    if names:
        ret.append(f"{f.full_name} 对 {names} 没有应该有的{'写入' if is_write else '读取'}")
    return ret

def read_write_check(token_info:TokenInfo, items:List[Tuple[Enum, List[Enum], List[Enum]]]) -> List[str]:
    layerouts = []
    for item in items:
        f = token_info.get_f(item[0])
        states_read = [token_info.state_map[e] for e in item[1]]
        states_write = [token_info.state_map[e] for e in item[2]]
        
        if item[0] in [ERC721_E_Require.transferFrom, ERC721_E_Require.safeTransferFrom, ERC721_E_Require.safeTransferFrom2]:
            enumerable_states = []
            for name in ['_ownedTokens','_ownedTokensIndex','_allTokens','_allTokensIndex']:
                state = token_info.c.get_state_variable_from_name(name)
                if state:
                    enumerable_states.append(state)
            states_read.extend(enumerable_states)
            states_write.extend(enumerable_states)

        layerouts.extend(func_only_op_state(f, READ_FLAG, states_read))
        layerouts.extend(func_only_op_state(f, WRITE_FLAG, states_write))
    return layerouts

WRITE_FLAG = True
READ_FLAG = False

msg_sender = SolidityVariableComposed("msg.sender")

class RequiredFuncNode(DecisionNode):
    def check(self, token_info: TokenInfo) -> NodeReturn: 
        def check_msg_sender(e:type[Enum]):       
            for ee in e._member_map_.values():
                if msg_sender not in token_info.get_f(ee).all_solidity_variables_read():
                    self.add_warn(f'{e.name}未读取msg.sender') 

        if token_info.is_erc20:
            check_msg_sender(ERC20_E_Require)
            items = [
                (ERC20_E_Require.transfer, [ERC20_E_view.balanceOf], [ERC20_E_view.balanceOf]),
                (ERC20_E_Require.approve, [], [ERC20_E_view.allowance]),
                (ERC20_E_Require.transferFrom, [ERC20_E_view.balanceOf,ERC20_E_view.allowance], [ERC20_E_view.balanceOf,ERC20_E_view.allowance])
            ]
        elif token_info.is_erc721:
            check_msg_sender(ERC721_E_Require)
            items = [
                (
                    ERC721_E_Require.approve,
                    [ERC721_E_view.ownerOf, ERC721_E_view.isApprovedForAll],
                    [ERC721_E_view.getApproved]
                ),
                (
                    ERC721_E_Require.setApprovalForAll,
                    [],
                    [ERC721_E_view.isApprovedForAll]
                ),
                (
                    ERC721_E_Require.transferFrom,
                    [ERC721_E_view.ownerOf, ERC721_E_view.isApprovedForAll, ERC721_E_view.getApproved, ERC721_E_view.balanceOf],
                    [ERC721_E_view.ownerOf, ERC721_E_view.getApproved, ERC721_E_view.balanceOf],
                ),
                (
                    ERC721_E_Require.safeTransferFrom,
                    [ERC721_E_view.ownerOf, ERC721_E_view.isApprovedForAll, ERC721_E_view.getApproved, ERC721_E_view.balanceOf],
                    [ERC721_E_view.ownerOf, ERC721_E_view.getApproved, ERC721_E_view.balanceOf],
                ),
                (
                    ERC721_E_Require.safeTransferFrom2,
                    [ERC721_E_view.ownerOf, ERC721_E_view.isApprovedForAll, ERC721_E_view.getApproved, ERC721_E_view.balanceOf],
                    [ERC721_E_view.ownerOf, ERC721_E_view.getApproved, ERC721_E_view.balanceOf],
                )
            ]

        layerouts = read_write_check(token_info, items)        
        if len(layerouts) == 0:
            self.add_info('标准方法读写集检查无异常')
        else:
            self.add_warns(layerouts)
        return NodeReturn.branch0
