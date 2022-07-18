from typing import List, Mapping
from slither.core.declarations import Contract, Function, SolidityVariableComposed
from slither.core.variables.state_variable import StateVariable

from .e import *

class BaseCheck:
    func: Mapping[E,Function]
    def __init__(self, c: Contract):
        self.c = c

    def _get_f_from_e(self, e:E):
        f = self.c.get_function_from_signature(e.sign)            
        if e.is_required:
            assert f, f'the contract {self.c.name} does not contain the method {e.sign}'
        if f:
            assert f in self.c.functions_entry_points
        return f

    def _get_view_state(self, e_view: E_view) -> StateVariable:
        """
        get the state which is based by totalSupply, balanceOf, allowance
        """
        f = self.c.get_function_from_signature(e_view.sign)
        if f:
            assert len(f.state_variables_read) == 1, 'the {} function read {} state'.format(e_view.name, len(f.state_variables_read))
            return f.state_variables_read[0]
        else:
            for s in self.c.state_variables:
                if s.name == e_view.name:
                    return s
            assert False, "the informantion about {} can not be found".format(e_view.name)


class Erc20BaseCheck(BaseCheck):
    def __init__(self, c: Contract):
        super().__init__(c)
        self.func: Mapping[ERC20_E,Function] = {}
        for e in ERC20_E._member_map_.values():
            f = self._get_f_from_e(e)
            if f:
                self.func[e] = f        
        
        self.totalSupply = self._get_view_state(ERC20_E_view.totalSupply)
        self.balance = self._get_view_state(ERC20_E_view.balanceOf)
        self.allowance = self._get_view_state(ERC20_E_view.allowance)

class Erc721BaseCheck(BaseCheck):
    def __init__(self, c: Contract):
        super().__init__(c)
        self.func: Mapping[ERC721_E,Function] = {}
        for e in ERC721_E._member_map_.values():
            f = self._get_f_from_e(e)
            if f:
                self.func[e] = f        
        
        self.balances = self._get_view_state(ERC721_E_view.balanceOf)
        self.owners = self._get_view_state(ERC721_E_view.ownerOf)
        self.tokenApprovals = self._get_view_state(ERC721_E_view.getApproved)
        self.operatorApprovals = self._get_view_state(ERC721_E_view.isApprovedForAll)