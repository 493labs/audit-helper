from typing import List, Mapping
from slither.core.declarations import Contract, Function
from slither.core.variables.state_variable import StateVariable

from core.base.analyze import BaseAnalyze
from .e import *

class BaseCheck(BaseAnalyze):
    def __init__(self, c: Contract):
        super().__init__(c)
        self.c: Contract = c
        self.func: Mapping[E,Function] = {}
        for e in E._member_map_.values():
            f = c.get_function_from_signature(e.sign)            
            if e.is_required:
                assert f
            if f:
                assert f in c.functions_entry_points
                self.func[e] = f
        
        self.totalSupply = self.__get_view_state(E_view.totalSupply)
        self.balance = self.__get_view_state(E_view.balanceOf)
        self.allowance = self.__get_view_state(E_view.allowance)

    def __get_view_state(self, e_view: E_view) -> StateVariable:
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

    def func_to_full_reachable_internal_funcs(self, f:Function) -> List[Function]:
        '''
        迭代获取方法可达到的内部调用（包含自己）
        '''
        return self._func_to_full_reachable_internal_funcs(f)
