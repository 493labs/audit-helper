from typing import List, Mapping, Tuple, Optional
from slither.core.declarations import Function
from slither.core.variables.state_variable import StateVariable
import graphviz as gv
from enum import Enum,unique

@unique
class View(Enum):
    In_Call = 1
    Ex_Call = 2
    All_Call = 3

class LeafViewWrapper:
    def __init__(self) -> None:
        self.__name_count:Mapping[str,int] = {}
        self.__fname_prefix_count:Mapping[Function,int] = {}

    def reset(self):
        self.__name_count:Mapping[str,int] = {}
        self.__fname_prefix_count:Mapping[Function,int] = {}

    def generate_view_fname(self, f: Function)->str:
        '''
        用于统一处理重名情况
        '''
        # 非函数情况直接返回其字符串
        if  not isinstance(f, Function|StateVariable):
            return str(f)
        if f not in self.__fname_prefix_count:
            if f.name not in self.__name_count:
                self.__name_count[f.name] = 0
            self.__fname_prefix_count[f] = self.__name_count[f.name]
            self.__name_count[f.name] += 1
        return '.' * self.__fname_prefix_count[f] + f.name

class ClusterDiGraph(gv.Digraph):
    def __init__(self, name: Optional[str] = None, is_root:bool=True) -> None:
        super().__init__(name, strict=is_root)
        if is_root:
            self.attr(fontsize='30', ranksep='2')
        self.__cluster_digraph: Mapping[str, gv.Digraph] = {}
        self.__dup_edge_record: Mapping[str, str] = {}
    

    def get_cluster_digraph_with_set_if_none(self, cluster_tag:str)->gv.Digraph: 
        if cluster_tag not in self.__cluster_digraph:
            cluster_dot = ClusterDiGraph('cluster_'+cluster_tag, is_root=False)   
            cluster_dot.attr(
                label = cluster_tag,
                fontsize = '25',
                style = 'filled'
            )
            cluster_dot.attr('node',
                shape = 'box',
                fontsize = '20'
            )
            self.__cluster_digraph[cluster_tag] = cluster_dot
        return self.__cluster_digraph[cluster_tag]
    def loop_get_cluster_digraph_with_set_if_none(self, cluster_path: List[str])->gv.Digraph:
        cur_graph = self       
        for cluster_tag in cluster_path: 
            cur_graph = cur_graph.get_cluster_digraph_with_set_if_none(cluster_tag)
        return cur_graph

    def add_cluster_node(self, cluster_path: List[str], name: str) -> None:
        self.loop_get_cluster_digraph_with_set_if_none(cluster_path).node(name)

    def add_edge(self, tail:str, head:str, label:str):
        '''
        多次调用时，将序号汇合在一起
        '''
        key = f'{tail}->{head}'
        if key not in self.__dup_edge_record:
            self.__dup_edge_record[key] = label            
        else:
            self.__dup_edge_record[key] = f'{self.__dup_edge_record[key]}\n{label}'
        self.edge(tail, head, self.__dup_edge_record[key])

        
    def gene_cluster_node(self):
        for cluster_dot in self.__cluster_digraph.values():
            cluster_dot.gene_cluster_node()
            self.subgraph(cluster_dot)

    def gene_fix_node(self, nodes:List[str], rank:str = 'max'):
        fix_dot = gv.Digraph()
        fix_dot.attr(rank=rank)
        for node in nodes:
            fix_dot.node(node)
        self.subgraph(fix_dot)
