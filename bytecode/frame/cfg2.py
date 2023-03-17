from typing import List, Mapping
import graphviz as gv
from mythril.disassembler.disassembly import Disassembly

class Node:
    def __init__(self, start_inst = None) -> None:
        self.start_inst = start_inst
        self.insts:List = []
        self.sorted:bool = False
        self.highlight = False
        self.uid = str(hash(self))

    def label(self)->str:
        if not self.sorted:
            self.insts.sort(key=lambda x:x['address'])
            self.sorted = True
        return '\n'.join([str(inst) for inst in [self.start_inst]+self.insts])
    
    def inject(self, graph:gv.Digraph, disassembly):
        if self.start_inst['address'] in disassembly.address_to_function_name:
            function_name = disassembly.address_to_function_name[self.start_inst['address']]
            graph.node(self.uid, label =  function_name + '\n' + self.label(), fontcolor = 'red')
        else:
            if self.highlight:
                graph.node(self.uid, label=self.label(), fontcolor = 'red')
            else:
                graph.node(self.uid, label=self.label())

class Edge:
    def __init__(self, node_from:Node, node_to:Node) -> None:
        self.node_from = node_from
        self.node_to = node_to

class CFG:
    def __init__(self, exec_paths:List[List], disassembly:Disassembly) -> None:
        # 目前只针对单个字节码
        self.exec_paths = exec_paths
        self.disassembly = disassembly
        self.start_to_node:Mapping[int, Node] = {}
        self.cur_node:Node = None
        self.edges:List[Edge] = []

    def analyze(self):
        for path in self.exec_paths:
            self.analyze_path(path)
            
    def analyze_path(self, path:List):
        assert len(path) > 0
        # 处理第一个指令
        if 0 not in self.start_to_node:
            self.start_to_node[0] = Node(path[0])
        self.cur_node = self.start_to_node[0]
        i = 0
        while i < len(path):
            if path[i]['opcode'] in ['JUMP','JUMPI'] and path[i+1]['opcode'] == 'JUMPDEST':
                if path[i] not in self.cur_node.insts:
                    self.cur_node.insts.append(path[i])
                dest_address = path[i+1]['address']
                # 前面对dest，可能会重复赋值
                # assert path[i]['dest'] == dest_address
                if dest_address not in self.start_to_node:
                    self.start_to_node[dest_address] = Node(path[i+1])
                self.edges.append(Edge(self.cur_node, self.start_to_node[dest_address]))
                i+=2
                self.cur_node = self.start_to_node[dest_address]
            elif path[i]['opcode'] in ['STOP','RETURN','SELFDESTRUCT','REVERT','INVALID']:
                self.cur_node.insts.append(path[i])
                i+=1
            elif path[i]['opcode'] in ['CALL','STATICCALL','SSTORE','SLOAD']:
                self.cur_node.insts.append(path[i])
                self.cur_node.highlight = True
                i+=1
            else:
                i+=1

    def graph(self):        
        g = gv.Digraph(strict=True)
        for edge in self.edges:
            edge.node_from.inject(g, self.disassembly)
            edge.node_to.inject(g, self.disassembly)
            g.edge(edge.node_from.uid, edge.node_to.uid)
        g.render(view=True)

