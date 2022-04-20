from typing import List
from slither.core.declarations import  Function, SolidityVariableComposed
from slither.core.variables.state_variable import StateVariable
from slither.core.cfg.node import NodeType,Node
from slither.slithir.operations import InternalCall,Index
from slither.slithir.variables import TemporaryVariable

from core.erc20.common.check_base import BaseCheck
from core.erc20.common.e import *

class StandardFuncCheck:
    def __init__(self, b:BaseCheck) -> None:
        self.b = b

    def _func_only_op_state(self, f: Function, is_write:bool, obj_indexs: List) -> bool:
        '''
        判断某方法是否只读取或写入了指定的state
        '''
        indexs = []
        for ff in self.b.func_to_full_reachable_internal_funcs(f):
            indexs.extend(ff.state_variables_written if is_write else ff.state_variables_read)
        indexs = list(set(indexs))

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

    def _check_mapping_detail(self,f:Function,s:StateVariable,is_write:bool,obj_indexss):
        # obj_indexss中的内容只需要为字符串("msg.sender")或者参数位置
        for i in range(len(obj_indexss)):
            for j in range(len(obj_indexss[i])):
                v = obj_indexss[i][j]
                obj_indexss[i][j] = SolidityVariableComposed(v) if isinstance(v,str) else f.parameters[v]

        depth = str(s.type).count("mapping")
        indexss = self.__get_mapping_indexs_op_by_func(f,s,is_write,depth)
        for indexs in indexss:
            if not self.__list_in_lists(indexs,obj_indexss):
                print(" {} 对 {} 有意料之外的{}：->{}".format(
                    f.name,
                    s.name,
                    "写入" if is_write else "读取",
                    '->'.join([index.name for index in indexs])
                ))
        for indexs in obj_indexss:
            if not self.__list_in_lists(indexs,indexss):
                print(" {} 对 {} 没有应该有的{}：->{}".format(
                    f.name,
                    s.name,
                    "写入" if is_write else "读取",
                    '->'.join([index.name for index in indexs])
                ))
    def __list_in_lists(self,l,ls)->bool:
        for l_ in ls:
            if len(l) == len(l_):
                match = True
                for i in range(len(l)):
                    if l[i] != l_[i]:
                        match = False
                        break
                if match:
                    return True
        return False
    # 获取方法对mapping变量读写的细节
    def __get_mapping_indexs_op_by_func(self,f:Function,s:StateVariable,is_write:bool,depth:int)->List[List]:
        # depth = str(s.type).count("mapping")
        indexss = []
        for n in f.nodes:
            for i in range(len(n.irs)):
                ir = n.irs[i]
                if isinstance(ir, Index) and ir.variable_left == s:
                    indexs = [self.__get_v_maybe_msgSender_func(n,i,ir.variable_right)]
                    # 递推获取索引
                    m_v, next_start_i = ir.lvalue, i+1
                    for _ in range(1,depth):
                        m_k, m_v, next_start_i = self.__get_mapping_index_v(n,next_start_i,m_v)
                        indexs.append(m_k)
                    indexss.append(indexs)
                if isinstance(ir,InternalCall) :
                    ic_rets = self.__get_mapping_indexs_op_by_func(ir.function,s,is_write,depth)
                    # 替换调用中的参数依赖
                    for m in range(len(ic_rets)):
                        for mm in range(depth):
                            for l in range(len(ir.arguments)):
                                if ic_rets[m][mm] == ir.function.parameters[l]:
                                    ic_rets[m][mm] = self.__get_v_maybe_msgSender_func(n,i,ir.arguments[l]) 
                    indexss.extend(ic_rets)
        return indexss    
    # 根据 node、起始i、mapping、获取mapping的索引
    def __get_mapping_index_v(self, n:Node, start_i:int, m_v):
        for i in range(start_i, len(n.irs)):
            ir = n.irs[i]
            if isinstance(ir, Index) and ir.variable_left == m_v:
                return self.__get_v_maybe_msgSender_func(n,i,ir.variable_right),ir.lvalue,i+1
        assert False
    def __get_v_maybe_msgSender_func(self,n:Node,i:int,v):
        # _msgSender() 的问题，简化处理，直接返回msg.sender
        if isinstance(v, TemporaryVariable):
            # 逆向寻找临时变量的值
            for j in range(i-1,-1,-1):
                ir_before = n.irs[j]
                if v == ir_before.lvalue \
                        and isinstance(ir_before,InternalCall) and self.__is_return_msg_sender(ir_before.function):
                    return SolidityVariableComposed("msg.sender")
        return v
    def __is_return_msg_sender(self,f:Function)->bool:
        return_nodes = []
        for n in f.nodes:
            if n.type == NodeType.RETURN:
                return_nodes.append(n)
        return len(return_nodes) == 1 and str(return_nodes[0].expression)=="msg.sender"

    def check_standard_func(self):
        self._func_only_op_state(self.b.func[E.transfer], READ_FLAG, [self.b.balance])
        self._func_only_op_state(self.b.func[E.transfer], WRITE_FLAG, [self.b.balance])
        self._func_only_op_state(self.b.func[E.approve], READ_FLAG, [])
        self._func_only_op_state(self.b.func[E.approve], WRITE_FLAG, [self.b.allowance])
        self._func_only_op_state(self.b.func[E.transferFrom], READ_FLAG, [self.b.balance, self.b.allowance])
        self._func_only_op_state(self.b.func[E.transferFrom], WRITE_FLAG, [self.b.balance, self.b.allowance])

        self._check_mapping_detail(self.b.func[E.transfer], self.b.balance, READ_FLAG, [['msg.sender'], [0]])
        self._check_mapping_detail(self.b.func[E.transfer], self.b.balance, WRITE_FLAG, [['msg.sender'], [0]])
        self._check_mapping_detail(self.b.func[E.approve], self.b.allowance, WRITE_FLAG, [['msg.sender', 0]])
        self._check_mapping_detail(self.b.func[E.transferFrom], self.b.balance, READ_FLAG, [[0], [1]])
        self._check_mapping_detail(self.b.func[E.transferFrom], self.b.balance, WRITE_FLAG, [[0], [1]])
        self._check_mapping_detail(self.b.func[E.transferFrom], self.b.allowance, READ_FLAG, [[0, 'msg.sender']])
        self._check_mapping_detail(self.b.func[E.transferFrom], self.b.allowance, WRITE_FLAG, [[0, 'msg.sender']])

        if E.burn in self.b.func:
            self._func_only_op_state(self.b.func[E.burn], READ_FLAG, [self.b.balance, self.b.totalSupply])
            self._func_only_op_state(self.b.func[E.burn], WRITE_FLAG, [self.b.balance, self.b.totalSupply])
            self._check_mapping_detail(self.b.func[E.burn], self.b.balance, READ_FLAG, [['msg.sender']])
            self._check_mapping_detail(self.b.func[E.burn], self.b.balance, WRITE_FLAG, [['msg.sender']])

        if E.increaseAllowance in self.b.func:
            self._func_only_op_state(self.b.func[E.increaseAllowance], READ_FLAG, [self.b.allowance])
            self._func_only_op_state(self.b.func[E.increaseAllowance], WRITE_FLAG, [self.b.allowance])
            self._check_mapping_detail(self.b.func[E.increaseAllowance], self.b.allowance, READ_FLAG, [['msg.sender', 0]])
            self._check_mapping_detail(self.b.func[E.increaseAllowance], self.b.allowance, WRITE_FLAG, [['msg.sender', 0]])
            
        if E.decreaseAllowance in self.b.func:
            self._func_only_op_state(self.b.func[E.decreaseAllowance], READ_FLAG, [self.b.allowance])
            self._func_only_op_state(self.b.func[E.decreaseAllowance], WRITE_FLAG, [self.b.allowance])
            self._check_mapping_detail(self.b.func[E.decreaseAllowance], self.b.allowance, READ_FLAG, [['msg.sender', 0]])
            self._check_mapping_detail(self.b.func[E.decreaseAllowance], self.b.allowance, WRITE_FLAG, [['msg.sender', 0]])

