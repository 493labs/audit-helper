from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_Require, TokenInfo, ERC20_E_view

from slither.core.declarations import Function, FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import Binary, BinaryType, LibraryCall
    

class TransferFeeCheck(TokenDecisionNode):
    # 统计一个function内有多少个对balance操作的operation，正常情况为两个一加一减，如果超出两个可能就是有向别的地址转钱
    def func_balance_operation(self, f:Function, balance: StateVariable) -> int:
            balance_op_count = 0 
            for ir in f.all_slithir_operations():
                if isinstance(ir, LibraryCall) and (ir.function.name == "sub" or ir.function.name == "add"):
                    for s in ir.node.state_variables_written:
                        if s == balance:
                            balance_op_count += 1
                elif isinstance(ir, Binary) and (ir.type in [BinaryType.ADDITION, BinaryType.SUBTRACTION]): 
                    for s in ir.node.state_variables_written:
                        if s == balance:
                            balance_op_count += 1
                            
            #for ic in f.internal_calls:
            #    if isinstance(ic, FunctionContract):
            #        balance_op_count += self.func_balance_operation(ic, balance)
            return balance_op_count
    
    
    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        func_es = []
        warns = []
        if token_info.is_erc20:
            func_es = [ERC20_E_Require.transfer, ERC20_E_Require.transferFrom]
            state_e = ERC20_E_view.balanceOf

        for func_e in func_es:
            balance_op_count = 0
            transfer_func = token_info.get_f(func_e)
            balance_state = token_info.state_map[state_e]
            balance_op_count = self.func_balance_operation(transfer_func, balance_state)
            if balance_op_count > 2:
                warns.append(f'{transfer_func.name} 存在收取手续费及相关参数的设置')
            
        if len(warns) == 0:
            self.add_info(f'未发现收取手续费及相关参数的设置')
        else:
            self.add_warns(warns)
        return NodeReturn.branch0

