from slither.core.declarations import Contract, Function
from core.base.analyze import BaseAnalyze
from core.base.graph import TreeGraph, LeafViewWrapper, View


class CallGraph(BaseAnalyze):
    def __init__(self, c: Contract) -> None:
        super().__init__(c)
        self.tree_graph = TreeGraph()
        self.leaf_view = LeafViewWrapper()

    def __rest(self):
        self.tree_graph.reset()
        self.leaf_view.reset()

    def generate_graph(self, view: View, is_single: bool = False, fname: str = ""):
        self.__rest()
        if is_single:
            fs = [f for f in self.c.functions_entry_points if f.name == fname]
            assert len(fs) == 1
            self.tree_graph.add_node(
                ['entry', fs[0].contract_declarer.name],
                self.leaf_view.generate_view_fname(fs[0])
            )
            self.__for_call(fs[0], view)
            self.tree_graph.generate_dot().render(self.c.name + '_' + fname + '_call.dot', 'output')
        else:
            for func in self.c.functions_entry_points:
                if func.view or func.pure:
                    continue
                self.tree_graph.add_node(
                    ['entry', func.contract_declarer.name],
                    self.leaf_view.generate_view_fname(func)
                )
                self.__for_call(func, view)
            self.tree_graph.generate_dot().render(self.c.name+'_' + view.name + '.dot', 'output')

    def __for_call(self, f: Function, view: View):
        fname = self.leaf_view.generate_view_fname(f)

        cur_internal_calls = self._func_to_internal_funcs(f)
        for call in cur_internal_calls:
            self.__for_call(call, view)

        for call in cur_internal_calls:
            if view in [View.In_Call, View.All_Call] or len(self._func_to_external_funcs(call)) > 0:
                call_name = self.leaf_view.generate_view_fname(call)
                self.tree_graph.add_node([call.contract_declarer.name], call_name)
                self.tree_graph.add_edge((fname, call_name))

        if view in [View.Ex_Call, View.All_Call]:
            cur_external_calls = self._func_to_external_funcs(f)
            for call_tuple in cur_external_calls:
                call_name = self.leaf_view.generate_view_fname(call_tuple[1])
                self.tree_graph.add_node(['out_call', call_tuple[0]], call_name)
                self.tree_graph.add_edge((fname, call_name))
