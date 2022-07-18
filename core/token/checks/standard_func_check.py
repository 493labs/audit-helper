from typing import List
from slither.core.declarations import  Function, SolidityVariableComposed

from ..common.check_base import Erc20BaseCheck, Erc721BaseCheck
from ..common.e import *

def func_only_op_state(f: Function, is_write:bool, obj_indexs: List):
    '''
    判断某方法是否只读取或写入了指定的state
    '''
    indexs = f.all_state_variables_written() if is_write else f.all_state_variables_read()

    for index in indexs:
        if index not in obj_indexs:
            print(" {} 对 {} 有意料之外的{}".format(
                f.name,
                index.name,
                "写入" if is_write else "读取"
            ))
    for index in obj_indexs:
        if index not in indexs:
            print(" {} 对 {} 没有应该有的{}".format(
                f.name,
                index.name,
                "写入" if is_write else "读取"
            ))

def func_need_read_msg_sendor(f:Function):
    all_solidity_variables_read = f.all_solidity_variables_read()
    assert SolidityVariableComposed("msg.sender") in all_solidity_variables_read, f'{f.name} does not read msg.sendor'

def erc20_check_standard_func(b:Erc20BaseCheck):
    func_need_read_msg_sendor(b.func[ERC20_E.transfer])
    func_need_read_msg_sendor(b.func[ERC20_E.approve])
    func_need_read_msg_sendor(b.func[ERC20_E.transferFrom])

    func_only_op_state(b.func[ERC20_E.transfer], READ_FLAG, [b.balance])
    func_only_op_state(b.func[ERC20_E.transfer], WRITE_FLAG, [b.balance])        
    func_only_op_state(b.func[ERC20_E.approve], READ_FLAG, [])
    func_only_op_state(b.func[ERC20_E.approve], WRITE_FLAG, [b.allowance])
    func_only_op_state(b.func[ERC20_E.transferFrom], READ_FLAG, [b.balance, b.allowance])
    func_only_op_state(b.func[ERC20_E.transferFrom], WRITE_FLAG, [b.balance, b.allowance])

    if ERC20_E.burn in b.func:
        func_need_read_msg_sendor(b.func[ERC20_E.burn])
        func_only_op_state(b.func[ERC20_E.burn], READ_FLAG, [b.balance, b.totalSupply])
        func_only_op_state(b.func[ERC20_E.burn], WRITE_FLAG, [b.balance, b.totalSupply])

    if ERC20_E.increaseAllowance in b.func:
        func_need_read_msg_sendor(b.func[ERC20_E.increaseAllowance])
        func_only_op_state(b.func[ERC20_E.increaseAllowance], READ_FLAG, [b.allowance])
        func_only_op_state(b.func[ERC20_E.increaseAllowance], WRITE_FLAG, [b.allowance])
        
    if ERC20_E.decreaseAllowance in b.func:
        func_need_read_msg_sendor(b.func[ERC20_E.decreaseAllowance])
        func_only_op_state(b.func[ERC20_E.decreaseAllowance], READ_FLAG, [b.allowance])
        func_only_op_state(b.func[ERC20_E.decreaseAllowance], WRITE_FLAG, [b.allowance])

def erc721_check_standard_func(b:Erc721BaseCheck):
    func_need_read_msg_sendor(b.func[ERC721_E.approve])
    func_need_read_msg_sendor(b.func[ERC721_E.setApprovalForAll])
    func_need_read_msg_sendor(b.func[ERC721_E.safeTransferFrom])
    func_need_read_msg_sendor(b.func[ERC721_E.safeTransferFrom2])
    func_need_read_msg_sendor(b.func[ERC721_E.transferFrom])

    func_only_op_state(b.func[ERC721_E.approve],READ_FLAG,[b.owners,b.operatorApprovals])
    func_only_op_state(b.func[ERC721_E.approve],WRITE_FLAG,[b.tokenApprovals])

    func_only_op_state(b.func[ERC721_E.setApprovalForAll],READ_FLAG,[])
    func_only_op_state(b.func[ERC721_E.setApprovalForAll],WRITE_FLAG,[b.operatorApprovals])

    func_only_op_state(b.func[ERC721_E.safeTransferFrom],READ_FLAG,[b.owners,b.operatorApprovals,b.tokenApprovals,b.balances])
    func_only_op_state(b.func[ERC721_E.safeTransferFrom],WRITE_FLAG,[b.tokenApprovals,b.owners,b.balances])
    func_only_op_state(b.func[ERC721_E.safeTransferFrom2],READ_FLAG,[b.owners,b.operatorApprovals,b.tokenApprovals,b.balances])
    func_only_op_state(b.func[ERC721_E.safeTransferFrom2],WRITE_FLAG,[b.tokenApprovals,b.owners,b.balances])
    func_only_op_state(b.func[ERC721_E.transferFrom],READ_FLAG,[b.owners,b.operatorApprovals,b.tokenApprovals,b.balances])
    func_only_op_state(b.func[ERC721_E.transferFrom],WRITE_FLAG,[b.tokenApprovals,b.owners,b.balances])


