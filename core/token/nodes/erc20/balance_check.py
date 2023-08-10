from typing import List
from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_view, TokenInfo

from slither.core.declarations import Function, Contract
from slither.slithir.operations import Binary, BinaryType
from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.cfg.node import NodeType
from slither.core.variables.state_variable import StateVariable


def balance_check_fail2(c:Contract, f: Function, balance: StateVariable) -> bool:
    # 是否存在balance减法表达式
    sub_balance_nodes = [node for node in f.all_nodes() for ir in node.irs if isinstance(ir, Binary) and ir.type is BinaryType.SUBTRACTION and balance in node.variables_written]
    
    if sub_balance_nodes:
        for node in f.all_nodes():
            #if node.contains_require_or_assert() or node.type == NodeType.IF:
            for ir in node.irs:
                # 是否存在比较IR，且IR.node读取的数据是balance
                if isinstance(ir, Binary) and (ir.type in [BinaryType.GREATER, BinaryType.GREATER_EQUAL, BinaryType.LESS, BinaryType.LESS_EQUAL]): 
                    balance_depends = [v for v in node.variables_read if is_dependent(v, balance, c)]
                    for d in balance_depends:
                        if d in node.variables_read:
                            return False
        return True


def balance_check_fail(f: Function) -> bool:
    # 是否存在减法表达式
    sub_irs = [ir for ir in f.all_slithir_operations() if isinstance(ir, Binary) and ir.type is BinaryType.SUBTRACTION]
    
    if sub_irs:
        for ir in f.all_slithir_operations():
            # 是否存在比较表达式
            if isinstance(ir, Binary) and (ir.type in [BinaryType.GREATER, BinaryType.GREATER_EQUAL, BinaryType.LESS, BinaryType.LESS_EQUAL]): 
                return False
        return True


class BalanceCheck(TokenDecisionNode):

    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        warns = []
        if token_info.is_erc20:
            balance_state = token_info.state_map[ERC20_E_view.balanceOf]
            for func in token_info.enum_to_state_to_funcs(ERC20_E_view.balanceOf):
                #if balance_check_fail2(token_info.c, func, balance_state):
                if balance_check_fail(func):  
                    warns.append(f'{func.name} 具有余额校验失效风险') 
                
        if len(warns) == 0:
            self.add_info(f'余额校验未发现异常')
        else:
            self.add_warns(warns)
        return NodeReturn.branch0