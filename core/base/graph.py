from mimetypes import init
from typing import List, Mapping, Tuple
from slither.core.declarations import Function
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
        if  not isinstance(f, Function):
            return str(f)
        if f not in self.__fname_prefix_count:
            if f.name not in self.__name_count:
                self.__name_count[f.name] = 0
            self.__fname_prefix_count[f] = self.__name_count[f.name]
            self.__name_count[f.name] += 1
        return '.' * self.__fname_prefix_count[f] + f.name

class ClusterNode:
    def __init__(self, tag: str, fnames: List[str], child_nodes: List) -> None:
        self.tag = tag
        self.fnames = fnames
        self.child_nodes = child_nodes
        # self.leaf_view = leaf_view
    
    def get_child(self,cluster_tag:str):
        for child in self.child_nodes:
            if child.tag == cluster_tag:
                return child
        return None

    def extend_fnames(self, fnames: List[str]):
        self.fnames.extend(fnames)

    def append_fname(self, fname:str):
        self.fnames.append(fname)

    def extend_childs(self, childs: List):
        self.child_nodes.extend(childs)

    def append_child(self, child):
        self.child_nodes.append(child)

    def generate_dot(self, as_root:bool) -> gv.Digraph:
        if as_root:
            dot = gv.Digraph(name= self.tag,strict=True, graph_attr={
                'fontsize': '30',
                'ranksep': '2'
            }) 
        else:
            dot = gv.Digraph(name='cluster_'+self.tag,graph_attr={
                'label': self.tag,
                'fontsize': '25',
                'style': 'filled'
            },node_attr={
                'shape':'box',
                'fontsize': '20'
            })

        for fname in self.fnames:
            dot.node(fname)
        for node in self.child_nodes:
            node: ClusterNode = node
            dot.subgraph(node.generate_dot(as_root=False))
        return dot

class TreeGraph:
    def __init__(self) -> None:        
        self.root: ClusterNode = ClusterNode('root',[],[])
        self.edges: List[Tuple[str,str]] = []

    def reset(self):
        self.root: ClusterNode = ClusterNode('root',[],[])
        self.edges: List[Tuple[str,str]] = []

    def add_edge(self, edge: Tuple[str,str]):
        self.edges.append(edge)
    def add_edges(self, edges: List[Tuple[str,str]]):
        self.edges.extend(edges)
    
    def __get_cluster(self,cluster_path:List[str])->ClusterNode:
        cur_node = self.root
        for cluster_tag in cluster_path:
            next_node:ClusterNode = cur_node.get_child(cluster_tag)
            if not next_node:
                next_node = ClusterNode(cluster_tag,[],[])
                cur_node.append_child(next_node)
            cur_node = next_node
        return cur_node
    def add_node(self,cluster_path:List[str],fname:str):
        self.__get_cluster(cluster_path).append_fname(fname)
    def add_nodes(self,cluster_path:List[str],fnames:List[str]):
        self.__get_cluster(cluster_path).extend_fnames(fnames)

    def generate_dot(self)->gv.Digraph:
        dot = self.root.generate_dot(as_root=True)
        dot.edges(self.edges)
        return dot
