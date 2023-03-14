from typing import List,Mapping
from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.laser.ethereum.util import get_instruction_index
from bytecode.frame.instrction import Instruction

class Node:
    def __init__(self, insts:List[Instruction] = None) -> None:
        self.insts = insts or []
        self.repeat_entry = False
        self.uid = str(hash(self))

    def label(self):
        if len(self.insts) > 1:
            view_insts = [self.insts[0]] \
                + [inst for inst in self.insts[1:-1] if inst['opcode'] in ['JUMP','JUMPI']] \
                + [self.insts[-1]]
            return '\n'.join([str(inst) for inst in view_insts])
        elif len(self.insts)  > 0:
            return str(self.insts[0])
        else:
            return 'instruction is empty'
class Edge:
    def __init__(self, node_from:Node, node_to:Node) -> None:
        self.node_from = node_from
        self.node_to = node_to

class CFG:
    def __init__(self) -> None:
        self.cur_node = Node()
        self.nodes:List[Node] = [self.cur_node]
        self.address_to_node:Mapping[int, Node] = {}
        self.jumpi_next_addr_to_node:Mapping[int, Node] = {}
        self.jump_dest_addr_to_node:Mapping[int,Node] = {}
        self.edges:List[Edge] = []

    def add_inst(self, global_state:GlobalState):
        instructions = global_state.environment.code.instruction_list
        cur_inst = instructions[global_state.mstate.pc]
        # if cur_inst['address'] in self.address_to_node:
        #     return

        if cur_inst['opcode'] in ['JUMP','JUMPI']:
            if cur_inst['opcode'] == 'JUMPI':
                cur_index = get_instruction_index(instructions,cur_inst['address'])
                next_address = instructions[cur_index+1]['address']
                if next_address not in self.jumpi_next_addr_to_node:
                    # jumpi的下一个不是jumpdest，但后续的cur_node可能会变化，所以需要记录所在节点
                    self.jumpi_next_addr_to_node[next_address] = self.cur_node
            dest_address = global_state.mstate.stack[-1].value
            assert dest_address
            # jump(i)指令增加dest信息
            cur_inst['dest'] = dest_address
            if dest_address in self.jump_dest_addr_to_node:
                # 有可能重复进入同一节点，但出来时为不同节点，类似函数调用
                self.jump_dest_addr_to_node[dest_address].repeat_entry = True
            else:
                # 除了第一个节点，其他的都以‘JUMPDEST’开始
                self.jump_dest_addr_to_node[dest_address] = Node([])
            self.edges.append(Edge(self.cur_node,self.jump_dest_addr_to_node[dest_address]))

        elif cur_inst['address'] in self.jump_dest_addr_to_node:
            self.cur_node = self.jump_dest_addr_to_node[cur_inst['address']]

        elif cur_inst['address'] in self.jumpi_next_addr_to_node:
            self.cur_node = self.jumpi_next_addr_to_node[cur_inst['address']]

        if not self.cur_node.repeat_entry or cur_inst['opcode']=='JUMP':
            self.cur_node.insts.append(cur_inst)
        
    def graph(self):
        import graphviz as gv
        g = gv.Digraph(strict=True)
        for edge in self.edges:
            g.node(edge.node_from.uid,label=edge.node_from.label())
            g.node(edge.node_to.uid,label=edge.node_to.label())
            g.edge(edge.node_from.uid, edge.node_to.uid)
        g.render(view=True)