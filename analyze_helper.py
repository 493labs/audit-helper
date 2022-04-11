from typing import List, Mapping, Tuple
from slither.core.declarations import Contract, Function, FunctionContract
from slither.slithir.operations import HighLevelCall, LowLevelCall, LibraryCall
import graphviz as gv
from enum import Enum,unique

@unique
class View(Enum):
    In = 1
    Out = 2
    All = 3

class AnalyzeHelper:
    def __init__(self, c:Contract) -> None:
        self.c = c
        self.c_entries: Mapping[str, List[Function]] = {}
        self.c_entries_view: Mapping[str, List[Function]] = {}
        self.c_inters: Mapping[str, List[Function]] = {}
        for f in c.functions_and_modifiers:
            if f in c.functions_entry_points:
                if f.view:
                    obj_map = self.c_entries_view
                else:
                    obj_map = self.c_entries
            else:
                obj_map = self.c_inters
            cname = f.contract_declarer.name
            if cname not in obj_map:
                obj_map[cname] = []
            obj_map[cname].append(f)

        f_call_internal_fs: Mapping[Function,List[Function]] = {}
        for f in c.functions_and_modifiers:
            # 下面的写法，当使用super调用时，上层方法的调用也出现了
            # all_internal_calls = f.all_internal_calls()
            # all_solidity_calls = f.all_solidity_calls()
            internal_calls = [
                call for call in f.internal_calls if call not in f.solidity_calls]
            modifiers = f.modifiers        
            for ff in internal_calls + modifiers:
                if ff.contract_declarer.kind == "library":
                    # 在调用父合约的方法时，父合约中本来的LibraryCall调用也出现在了internal_calls
                    continue
                if f not in f_call_internal_fs:
                    f_call_internal_fs[f] = []
                f_call_internal_fs[f].append(ff) 
        self.f_call_internal_fs = f_call_internal_fs

        f_call_external_fs: Mapping[Function,List[Tuple[str,Function]]] = {}
        for f in c.functions_and_modifiers:
            for node in f.nodes:
                for ir in node.irs:
                    if isinstance(ir, HighLevelCall) and not isinstance(ir, LibraryCall):
                        if f not in f_call_external_fs:
                            f_call_external_fs[f] = []
                        # 使用this调用自身方法时ir.destination.type.type没有name
                        f_call_external_fs[f].append((str(ir.destination.type.type),ir.function))
                    if isinstance(ir, LowLevelCall):
                        if f not in f_call_external_fs:
                            f_call_external_fs[f] = []
                        f_call_external_fs[f].append(('low level call',ir.function_name))

        self.f_call_external_fs = f_call_external_fs

        self.external_c_funcs: Mapping[str, List[Function]] = {}

    name_count:Mapping[str,int] = {}
    fname_prefix_count:Mapping[Function,int] = {}
    def __get_view_fname(self, f: Function)->str:
        '''
        用于统一处理重名情况
        '''
        # 非函数情况直接返回其字符串
        if  not isinstance(f, Function):
            return str(f)
        if f not in self.fname_prefix_count:
            if f.name not in self.name_count:
                self.name_count[f.name] = 0
            self.fname_prefix_count[f] = self.name_count[f.name]
            self.name_count[f.name] += 1
        return '.' * self.fname_prefix_count[f] + f.name

    def __add_subdot(self, dot:gv.Digraph, cname:str, funcs:List[Function]):
        subdot = gv.Digraph(name='cluster_'+cname,graph_attr={
            'label': cname,
            'fontsize': '25',
            'style': 'filled'
        },node_attr={
            'shape':'box',
            'fontsize': '20'
        })
        for f in funcs:
            subdot.node(self.__get_view_fname(f))
        dot.subgraph(subdot)

    def analyze_entries(self):
        dot = gv.Digraph(name='root',strict=True, graph_attr={
            'label': self.c.name+' entries which can change state',
            'fontsize': '30'
        })   

        for cname,funcs in self.c_entries.items():
            self.__add_subdot(dot, cname, funcs)

        dot.render(self.c.name+'_entries'+'.dot', 'output')

    def __yield_call_dot_elements(self, f, edges, out_edges, c_funcs, out_c_funcs:Mapping[str,List[Function]], view:View):
        # 外部调用
        if view == View.Out or view == View.All:
            if f in self.f_call_external_fs:
                for (out_c, out_func) in self.f_call_external_fs[f]:
                    out_edges.append((f,out_func))
                    if out_c not in out_c_funcs:
                        out_c_funcs[out_c] = []
                    out_c_funcs[out_c].append(out_func)        
        # 内部调用
        if f in self.f_call_internal_fs:
            for in_func in self.f_call_internal_fs[f]:
                if view == View.Out and \
                     in_func not in self.f_call_external_fs:
                    continue
                edges.append((f, in_func))
                cname = in_func.contract_declarer.name
                if cname not in c_funcs:
                    c_funcs[cname] = []
                c_funcs[cname].append(in_func)
                # 迭代
                self.__yield_call_dot_elements(in_func, edges, out_edges, c_funcs, out_c_funcs, view)

    def analyze_call(self, view:View, is_single:bool=False, fname:str=""):
        dot = gv.Digraph(name='root',strict=True, graph_attr={
            'label': self.c.name+' call graph from entries which can change state',
            'fontsize': '30',
            'ranksep': '2'
        }) 
        # 控制方向
        # if (view == View.Out or view == View.All) and not is_single:
        #     dot.attr('graph',{
        #         "rankdir": 'LR'
        #     })

        # 获取画图所需数据
        entries = []
        if is_single:
            fs = [f for f in self.c.functions_entry_points if f.name == fname]
            assert len(fs) == 1
            entries.extend(fs)
        else:
            for funcs in self.c_entries.values():
                entries.extend(funcs)
        edges: List[Tuple[Function,Function]]  = []
        out_edges: List[Tuple[Function,Function]] = []
        c_funcs: Mapping[str, List[Function]] = {}
        out_c_funcs: Mapping[str,List[Function]] = {}
        for f in entries:
            self.__yield_call_dot_elements(f,edges,out_edges,c_funcs,out_c_funcs,view)

        # 入口方法
        entry_dot = gv.Digraph(name='cluster_entry', graph_attr={
            'label': 'entries',
            'fontsize': '30',
            'style': 'filled'
        }) 
        if is_single:
            entry_dot.attr('node',{
                'shape':'box',
                'fontsize': '20'
            })
            entry_dot.node(self.__get_view_fname(entries[0]))
        else:
            for cname,funcs in self.c_entries.items():
                self.__add_subdot(entry_dot, cname, funcs)
        dot.subgraph(entry_dot)

        # 内部调用
        for cname,funcs in c_funcs.items():
            if cname == 'ContextUpgradeable':
                continue
            self.__add_subdot(dot, cname, funcs)
        for edge in edges:
            if edge[1].name == '_msgSender':
                continue
            dot.edge(self.__get_view_fname(edge[0]),self.__get_view_fname(edge[1]))
        
        # 外部调用
        if view == View.Out or view == View.All:
            out_call_dot = gv.Digraph(name='cluster_out_call', graph_attr={
                'label': 'out calls',
                'fontsize': '30',
                'style': 'filled'
            }) 
            for cname,funcs in out_c_funcs.items():
                self.__add_subdot(out_call_dot, cname, funcs)
            dot.subgraph(out_call_dot)
            
            for edge in out_edges:
                dot.edge(self.__get_view_fname(edge[0]),self.__get_view_fname(edge[1]))

        if is_single:
            dot.render(self.c.name + '_' + fname +'_' + view.name +'_call.dot', 'output')
        else:
            dot.render(self.c.name+'_'+ view.name +'_call.dot', 'output')



