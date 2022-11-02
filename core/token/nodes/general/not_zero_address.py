from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_view, ERC721_E_view, TokenInfo

from slither.core.solidity_types import ElementaryType
from slither.slithir.operations import InternalCall
from slither.core.declarations import Function

class NotZeroAddress(TokenDecisionNode):

    def token_check(self, token_info: TokenInfo) -> NodeReturn:

        def f_param_can_zero(f:Function)->bool:
            address_params = [p for p in f.parameters if isinstance(p.type, ElementaryType) and p.type.type == "address"]
            if not address_params:
                return False
            
            for param in address_params:
                cur_address_param_can_zero = True
                for node in f.nodes:
                    if node.is_conditional(False) \
                      and param in node.local_variables_read :
                        # and ('address(0)' in str(node.expression) or 'address(0x0)' in str(node.expression)):                          
                        cur_address_param_can_zero = False
                        break
                    if node.internal_calls:
                        # 内部调用情况
                        for ir in node.irs:
                            if isinstance(ir, InternalCall) and param in ir.arguments and not f_param_can_zero(ir.function):
                                cur_address_param_can_zero = False
                                break
                        if not cur_address_param_can_zero:
                            break

                if cur_address_param_can_zero:
                    return True
            return False


        if token_info.is_erc20:
            fs = set(token_info.enum_to_state_to_funcs(ERC20_E_view.balanceOf))
            fs |= set(token_info.enum_to_state_to_funcs(ERC20_E_view.allowance))
        if token_info.is_erc721:
            fs = set(token_info.enum_to_state_to_funcs(ERC721_E_view.balanceOf))
            fs |= set(token_info.enum_to_state_to_funcs(ERC721_E_view.getApproved))
            fs |= set(token_info.enum_to_state_to_funcs(ERC721_E_view.isApprovedForAll))
            fs |= set(token_info.enum_to_state_to_funcs(ERC721_E_view.ownerOf))

        f_ps_can_zero = []
        for f in fs:
            if f.is_constructor or f.view or f.pure or not f.all_state_variables_written():
                continue
            if f_param_can_zero(f):
                f_ps_can_zero.append(f)
            
        if f_ps_can_zero:
            fnames = ','.join([f.name for f in f_ps_can_zero])
            self.add_warn_info(f'{fnames} 存在地址参数未进行校验')
        else:
            self.add_info(f'地址参数检查未见异常')

        return NodeReturn.branch0