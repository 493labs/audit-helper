from typing import Mapping, List, Union
from copy import deepcopy, copy
from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable
import slither.core.solidity_types as solidity_types
from slither.core.cfg.node import NodeType

from core.symbolic.types import SolAddress
from core.symbolic.z3_helper import simplify
import z3


class WorldState:
    __contracts: Mapping[SolAddress, Contract]
    __storage: Mapping[str, any]
    __constraints: List[z3.ExprRef]

    def __init__(self, contracts = {}, storage = {}, constraints = []) -> None:
        self.__contracts = contracts
        self.__storage = storage
        self.__constraints = constraints

    def get_domain(self, address:SolAddress):
        return f"wstate.{address}"

    def get_key(self, address:SolAddress, ir_v:Union[str, StateVariable], key_additions:List=None ):
        prefix = self.get_domain(address)
        if isinstance(ir_v, str):
            return f"{prefix}.{ir_v}"
        
        elif isinstance(ir_v, StateVariable):
            if isinstance(ir_v.type, solidity_types.ElementaryType):
                return f"{prefix}.{ir_v.name}"
            
            elif isinstance(ir_v.type, solidity_types.MappingType):
                addition = ".".join([str(key_addition) for key_addition in key_additions])
                return f"{prefix}.{ir_v.name}.{addition}"
            else:
                assert False, "未支持的类型"
        assert False, "输入有误"

    def set_storage(self, address:SolAddress, ir_v:Union[str, StateVariable], val, key_additions:List=None):
        key = self.get_key(address, ir_v, key_additions)
        self.__storage[key] = val

    def get_storage(self, address:SolAddress, ir_v:Union[str, StateVariable], key_additions:List=None):
        key = self.get_key(address, ir_v, key_additions)
        if key not in self.__storage:
            if isinstance(ir_v, StateVariable) and ir_v.initialized:
                v = ir_v.node_initialization.irs[-1].rvalue
                return v
            return 0
        return self.__storage[key]
    
    def get_storage_by_key(self, key:str):
        assert isinstance(key, str)
        if key not in self.__storage:
            return 0
        return self.__storage[key]
    
    def get_contract(self, addr:SolAddress)->Contract:
        assert addr in self.__contracts
        return self.__contracts[addr]
    
    def set_contract(self, addr:SolAddress, c:Contract):
        assert addr not in self.__contracts
        self.__contracts[addr] = c

    def add_constraint(self, constraint):
        self.__constraints.append(simplify(constraint)) 

    def get_constraints(self):
        return self.__constraints

        
    def __deepcopy__(self, _)->"WorldState":
        return WorldState(copy(self.__contracts),copy(self.__storage),copy(self.__constraints))
