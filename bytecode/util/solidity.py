from mythril.solidity.soliditycontract import SolidityContract

import os

from core.utils.change_solc_version import change_solc_version

def get_contract(solc_dir:str, contract_path:str, contract_name:str=None)->SolidityContract:
    if solc_dir and len(solc_dir) > 0:
        cur_dir = os.getcwd()
        os.chdir(solc_dir)
        change_solc_version(contract_path)
        contract = SolidityContract(contract_path, contract_name)
        os.chdir(cur_dir)
    else:
        change_solc_version(contract_path)
        contract = SolidityContract(contract_path, contract_name)
    return contract
