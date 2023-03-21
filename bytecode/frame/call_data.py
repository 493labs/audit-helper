from mythril.laser.ethereum.state.calldata import SymbolicCalldata
from typing import List
from eth_utils.abi import function_signature_to_4byte_selector
from mythril.laser.smt import symbol_factory, Bool

def gene_calldata_contraints(call_data: SymbolicCalldata, function_signature: str) -> List[Bool]:
    constraints = [] # Constraints()
    func_hash = function_signature_to_4byte_selector(function_signature)
    for i in range(4):
        constraint =  call_data[i] == symbol_factory.BitVecVal(func_hash[i],8)
        
        constraints.append(constraint)
    return constraints