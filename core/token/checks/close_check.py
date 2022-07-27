from typing import List
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import SolidityCall

from ..common.check_base import BaseCheck, Erc20BaseCheck, Erc721BaseCheck
from ..common.e import *


def close_check(b:BaseCheck, allow_es:List, s:StateVariable):
    funcs = []
    for f in b.c.functions_entry_points:
        if not f.is_constructor:
            if s in f.all_state_variables_written():
                funcs.append(f)
    allow_funcs = [b.func[e] for e in allow_es if e in b.func]

    for f in funcs:
        if f not in allow_funcs:
            print("未知方法 {} 对 {} 进行了写操作".format(f.name, s.name))

def erc20_check_close(b:Erc20BaseCheck):
    # balance
    allow_es = [ERC20_E.transfer, ERC20_E.transferFrom, ERC20_E.burn]
    close_check(b, allow_es, b.balance)

    # allowance
    allow_es = [ERC20_E.approve, ERC20_E.transferFrom, ERC20_E.increaseAllowance, ERC20_E.decreaseAllowance]
    close_check(b, allow_es, b.allowance)

def erc721_check_close(b:Erc721BaseCheck):
    # owners
    allow_es = [ERC721_E.safeTransferFrom, ERC721_E.safeTransferFrom2, ERC721_E.transferFrom]
    close_check(b, allow_es, b.owners)

    # balances
    allow_es = [ERC721_E.safeTransferFrom, ERC721_E.safeTransferFrom2, ERC721_E.transferFrom]
    close_check(b, allow_es, b.balances)

    # tokenApprovals
    allow_es = [ERC721_E.safeTransferFrom, ERC721_E.safeTransferFrom2, ERC721_E.transferFrom, ERC721_E.approve]
    close_check(b, allow_es, b.tokenApprovals)

    # operatorApprovals
    allow_es = [ERC721_E.setApprovalForAll]
    close_check(b, allow_es, b.operatorApprovals)


def check_asm_s(b: BaseCheck):
    '''
    若程序中带有sload和sstore的汇编指令，则其行为具有很大的不确定性
    '''
    for f in b.c.functions_entry_points:
        for ir in f.all_slithir_operations():
            if isinstance(ir, SolidityCall) and ir.function.name.startswith("sload") :
                print(f" {f.name} 使用了 asm 的 sload ，功能未知")
            if isinstance(ir, SolidityCall) and ir.function.name.startswith("sstore"):
                print(f" {f.name} 使用了 asm 的 sstore ，功能未知")
                    

