from typing import List, Tuple

from slither.analyses.data_dependency.data_dependency import is_dependent_ssa
from slither.core.cfg.node import Node
from slither.core.declarations import Function, Contract
from slither.core.declarations.solidity_variables import (
    SolidityVariable,
    SolidityFunction,
    SolidityVariableComposed,
)
from slither.core.variables.variable import Variable
from slither.slithir.operations import BinaryType, Binary
from slither.slithir.operations import SolidityCall

from core.frame.base_node import DecisionNode,NodeReturn
from core.frame.contract_info import ContractInfo

def collect_return_values_of_bad_PRNG_functions(f: Function) -> List:
    values_returned = []
    for n in f.nodes:
        for ir in n.irs_ssa:
            if (
                isinstance(ir, SolidityCall)
                and ir.function == SolidityFunction("blockhash(uint256)")
                and ir.lvalue
            ):
                values_returned.append(ir.lvalue)
    return values_returned

def contains_bad_PRNG_sources(func: Function, blockhash_ret_values: List[Variable]) -> List[Node]:
    """
         Check if any node in function has a modulus operator and the first operand is dependent on block.timestamp, now or blockhash()
    Returns:
        (nodes)
    """
    ret = set()
    for node in func.nodes:
        for ir in node.irs_ssa:
            if isinstance(ir, Binary) and ir.type == BinaryType.MODULO:
                var_left = ir.variable_left
                if not isinstance(var_left, (Variable, SolidityVariable)):
                    continue
                if is_dependent_ssa(
                    var_left, SolidityVariableComposed("block.timestamp"), func
                ) or is_dependent_ssa(var_left, SolidityVariable("now"), func):
                    ret.add(node)
                    break

                for ret_val in blockhash_ret_values:
                    if is_dependent_ssa(var_left, ret_val, func):
                        ret.add(node)
                        break
    return list(ret)

def detect_bad_PRNG(contract: Contract) -> List[Tuple[Function, List[Node]]]:
    blockhash_ret_values = []
    for f in contract.functions:
        blockhash_ret_values += collect_return_values_of_bad_PRNG_functions(f)
    ret: List[Tuple[Function, List[Node]]] = []
    for f in contract.functions:
        bad_prng_nodes = contains_bad_PRNG_sources(f, blockhash_ret_values)
        if bad_prng_nodes:
            ret.append((f, bad_prng_nodes))
    return ret

class WeakPrng(DecisionNode):

    def check(self, contract_info: ContractInfo) -> NodeReturn:
        values = detect_bad_PRNG(contract_info.c)
        for func, _ in values:
            self.add_warn(f'{func.name} 使用了弱随机数据源')
        return NodeReturn.branch0