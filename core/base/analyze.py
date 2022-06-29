from typing import List, Mapping, Tuple
from slither.core.declarations import Contract, Function
from slither.core.cfg.node import Node
from slither.slithir.operations import HighLevelCall, LowLevelCall, LibraryCall


class BaseAnalyze:
    def __init__(self, c:Contract) -> None:
        self.c = c
        self.__func_to_internal_funcs: Mapping[Function, List[Function]] = {}
        self.__func_to_reachable_internal_funcs: Mapping[Function, List[Function]] = {}
        self.__func_to_external_funcs: Mapping[Function, List[Tuple[str, Function]]] = {}
        self.__func_to_reachable_external_funcs: Mapping[Function, List[Tuple[str, Function]]] = {}
        
    def _func_to_internal_funcs(self, f:Function) -> List[Function]:
        '''
        获取方法的内部调用
        '''
        if f not in self.__func_to_internal_funcs:
            calls = []
            # 下面的写法，当使用super调用时，上层方法的调用也出现了
            # all_internal_calls = f.all_internal_calls()
            # all_solidity_calls = f.all_solidity_calls()
            internal_calls = [
                call for call in f.internal_calls if call not in f.solidity_calls]
            # modifiers = f.modifiers
            
            for ff in internal_calls:
                if ff.contract_declarer.kind == "library":
                    # 在调用父合约的方法时，父合约中本来的LibraryCall调用也出现在了internal_calls
                    continue
                calls.append(ff)
            self.__func_to_internal_funcs[f] = calls
        return self.__func_to_internal_funcs[f]

    def _func_to_ordered_internal_funcs(self, f:Function) -> List[Tuple[Function,str]]:
        '''
        获取方法的内部调用(包含源代码行号)，多次调用同一个内部调用时，有重复
        '''
        if f not in self.__func_to_internal_funcs:
            calls = []
            # 去除构造函数的情况
            # modifiers也会出现在node中
            # calls.extend([ff for ff in f.modifiers if isinstance(ff, Function)])
            for node in f.nodes:
                ffs = [ff for ff in node.internal_calls if ff not in node.solidity_calls]
                for ff in ffs:
                    calls.append([ff,node.source_mapping_str])
            self.__func_to_internal_funcs[f] = calls
        return self.__func_to_internal_funcs[f]
        
    def _func_to_reachable_internal_funcs(self, f:Function) -> List[Function]:
        '''
        迭代获取方法可达到的内部调用（不包含自己）
        '''
        if  f not in self.__func_to_reachable_internal_funcs:
            calls = []
            cur_calls = self._func_to_internal_funcs(f)
            calls.extend(cur_calls)
            for call in cur_calls:
                calls.extend(self._func_to_reachable_internal_funcs(call))            
            self.__func_to_reachable_internal_funcs[f] = list(set(calls))
        return self.__func_to_reachable_internal_funcs[f]

    def _func_to_full_reachable_internal_funcs(self, f:Function) -> List[Function]:
        '''
        迭代获取方法可达到的内部调用（包含自己）
        '''
        return [f] + self._func_to_reachable_internal_funcs(f)
        

    def _func_to_external_funcs(self, f:Function, skip_dup:bool=True) -> List[Tuple[str, Function, str]]:
        ''' 
        获取方法的外部调用，包含源代码行号
        '''        
        if  f not in self.__func_to_external_funcs:
            calls:List[Tuple[str,Function]] = []
            for node in f.nodes:
                for ir in node.irs:
                    if isinstance(ir, HighLevelCall) and not isinstance(ir, LibraryCall):
                        # 使用this时特殊处理
                        if ir.destination.name == 'this':
                            calls.append(('this','o.'+ir.function.name,node.source_mapping_str))
                        else:
                            calls.append((str(ir.destination.type.type),ir.function,node.source_mapping_str))
                    if isinstance(ir, LowLevelCall):
                        calls.append(('low level call',ir.function_name,node.source_mapping_str)) 
                    if isinstance(ir, LibraryCall) and str(ir.destination)=='SafeERC20':
                        calls.append((str(ir.destination), ir.function_name, node.source_mapping_str))
            self.__func_to_external_funcs[f] = self.__dup_external_calls(calls)  if skip_dup else  calls        
        return self.__func_to_external_funcs[f]

    def _func_to_reachable_external_funcs(self, f:Function) -> List[Tuple[str, Function]]:
        '''
        迭代获取方法可达到的外部调用
        '''
        if f not in self.__func_to_reachable_external_funcs:
            ex_calls = []
            ex_calls.extend(self._func_to_external_funcs(in_call))
            for in_call in self._func_to_internal_funcs(f):
                ex_calls.extend(self._func_to_reachable_external_funcs(in_call))
            self.__func_to_reachable_external_funcs[f] = self.__dup_external_calls(ex_calls)
        return self.__func_to_reachable_external_funcs(f)

    def __dup_external_calls(self, calls:List[Tuple[str,Function]]) -> List[Tuple[str,Function]]:
        '''
        去除重复的外部调用
        '''
        new_calls = []
        dup_map = {}
        for call_tup in calls:
            if call_tup[0] not in dup_map:
                new_calls.append(call_tup)
                dup_map[call_tup[0]] = [call_tup[1]]
            else:
                if call_tup[1] not in dup_map[call_tup[0]]:
                    new_calls.append(call_tup)
                    dup_map[call_tup[0]].append(call_tup[1])
        return new_calls
