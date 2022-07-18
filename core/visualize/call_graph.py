from typing import List, Tuple
from slither.core.declarations import Contract, Function, FunctionContract
from .analyze import BaseAnalyze
from .graph import LeafViewWrapper, View, ClusterDiGraph


class CallGraph(BaseAnalyze):
    def __init__(self, c: Contract) -> None:
        super().__init__(c)
        self.cluster_graph = ClusterDiGraph('root')
        self.leaf_view = LeafViewWrapper()
        self.fixed_node: List[str] = []

    def __rest(self):
        self.cluster_graph = ClusterDiGraph('root')
        self.leaf_view.reset()
        self.fixed_node = []

    def generate_graph(self, view: View, is_single: bool = False, fname: str = ""):
        self.__rest()

        for_loop:Tuple(List[Function],str) = ()
        if is_single:
            fs = [f for f in self.c.functions_entry_points if f.name == fname]
            assert len(fs) == 1, f'{fname} is not on the entry points'
            for_loop =(fs, f'{self.c.name}_func_{fs[0].name}_call.dot')
        else:
            fs = [f for f in self.c.functions_entry_points if not f.view and not f.pure]
            for_loop = (fs, f'{self.c.name}_{view.name}.dot')

        for f in for_loop[0]:
            f:FunctionContract = f
            self.cluster_graph.add_cluster_node(
                ['entry', f.contract_declarer.name],
                self.leaf_view.generate_view_fname(f)
            )
            self.__for_call(f, view, False, is_single)
        if len(self.fixed_node) > 0:
            self.cluster_graph.gene_fix_node(self.fixed_node)
        self.cluster_graph.gene_cluster_node()
        self.cluster_graph.attr(rankdir='LR')
        # self.cluster_graph.view()
        self.cluster_graph.render(for_loop[1],'output')

    def __for_call(self, f: Function, view: View, open_state:bool = False, open_sequece:bool = False, depths:List[int] = []):
        fname = self.leaf_view.generate_view_fname(f)

        cur_internal_calls = self._func_to_ordered_internal_funcs(f)
        for i in range(len(cur_internal_calls)):
            self.__for_call(cur_internal_calls[i][0],view, open_state, open_sequece, depths + [i])

        if open_state:
            # library call  也可以改变状态，待完善
                    
            for s in f.state_variables_written:
                state_name = self.leaf_view.generate_view_fname(s)
                if s in f.state_variables_read:
                    self.cluster_graph.edge(fname, state_name, dir = 'both')
                else:
                    self.cluster_graph.edge(fname,state_name)
                self.fixed_node.append(state_name)
            for s in f.state_variables_read:
                if s not in f.state_variables_written and not s.is_constant:
                    state_name = self.leaf_view.generate_view_fname(s)
                    self.cluster_graph.edge(state_name, fname)
                    self.fixed_node.append(state_name)

        for i in range(len(cur_internal_calls)):
            call = cur_internal_calls[i][0]
            if view in [View.In_Call, View.All_Call] or len(self._func_to_external_funcs(call)) > 0:
                if call.name == '_msgSender':
                    continue
                call_name = self.leaf_view.generate_view_fname(call)
                self.cluster_graph.add_cluster_node([call.contract_declarer.name], call_name)
                if open_sequece:
                    self.cluster_graph.add_edge(fname, call_name, '#'+cur_internal_calls[i][1].split('#')[1])
                else:
                    self.cluster_graph.edge(fname, call_name)
                
                
        if view in [View.Ex_Call, View.All_Call]:
            cur_external_calls = self._func_to_external_funcs(f, skip_dup = False)
            for i in range(len(cur_external_calls)):
                call_tuple = cur_external_calls[i]

                call_name = self.leaf_view.generate_view_fname(call_tuple[1])
                self.cluster_graph.add_cluster_node(['out_call', call_tuple[0]], call_name)
                if open_sequece:
                    self.cluster_graph.add_edge(fname, call_name, '#'+call_tuple[2].split('#')[1])
                else:
                    self.cluster_graph.edge(fname, call_name)

    def gene_wt_graph(self):
        self.__rest()
        for s in self.c.state_variables:
            self.cluster_graph.add_cluster_node(['State', s.contract.name], s.name)
        for f in self.c.functions_entry_points:
            if f.is_constructor:
                continue
            for s in f.all_state_variables_written():
                if s in f.all_state_variables_read():
                    self.cluster_graph.edge(f.name, s.name, color='orange', dir = 'both')
                else:
                    self.cluster_graph.edge(f.name,s.name, color='red')
            for s in f.all_state_variables_read():                
                if s.is_constant or s.is_immutable:
                    continue
                if s not in f.all_state_variables_written():
                    self.cluster_graph.edge(s.name, f.name, color = 'green')

        self.cluster_graph.attr('graph',rankdir='LR')
        # self.cluster_graph.gene_fix_node(['transfer','transferFrom'],'min')
        self.cluster_graph.gene_cluster_node()

        # self.cluster_graph.view()
        self.cluster_graph.render(f'{self.c.name}_write_read_graph.dot', 'output')
