from configparser import ConfigParser
import os
from slither import Slither
import sys
sys.path.append('.')
from core.call_graph import CallGraph, View

if __name__ == "__main__":
    config = ConfigParser()
    config.read('./config.ini', 'utf-8')
    contract_root_path = config.get('target', 'contract_root_path')
    contract_path = config.get('target', 'contract_path')
    contract_name = config.get('target', 'contract_name')
    function_names = config.get('target', 'function_names')
    analyze_global = config.getboolean('target', 'analyze_global')
    analyze_function = config.getboolean('target', 'analyze_function')

    os.chdir(contract_root_path)
    sli = Slither(contract_path)

    cs = sli.get_contract_from_name(contract_name)
    assert len(cs) == 1
    c = cs[0]

    analyze = CallGraph(c)
    if analyze_global:
        analyze.generate_graph(View.In_Call)
        analyze.generate_graph(View.Ex_Call)
        analyze.generate_graph(View.All_Call)
    if analyze_function:
        fnames = [s.strip() for s in function_names.split(',')]
        for fname in function_names.split(','):
            fname = fname.strip()
            analyze.generate_graph(View.All_Call, True, fname)
