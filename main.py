from configparser import ConfigParser
import os
from slither import Slither
from slither.core.declarations import Contract
import sys
sys.path.append('.')
from core.call_graph import CallGraph, View
from core.external_call import ExternalCall

BASE_INFO = 'base-info'
CALL_GRAPH = 'call-graph'
EXTERNAL_CALL = 'external-call'
OPEN = 'open'

def call_graph(config:ConfigParser, c:Contract):    
    function_names = config.get(CALL_GRAPH, 'function_names')
    analyze_global = config.getboolean(CALL_GRAPH, 'analyze_global')
    analyze_function = config.getboolean(CALL_GRAPH, 'analyze_function')
    analyze = CallGraph(c)
    if analyze_global:
        analyze.generate_graph(View.In_Call)
        analyze.generate_graph(View.Ex_Call)
        analyze.generate_graph(View.All_Call)
    if analyze_function:
        for fname in function_names.split(','):
            fname = fname.strip()
            analyze.generate_graph(View.All_Call, True, fname)

def external_call(config:ConfigParser, c:Contract):
    ex_call_analyze = ExternalCall(c)
    ex_call_analyze.find_dangerous_ex_call()

if __name__ == "__main__":
    config = ConfigParser()
    config.read('./config.ini', 'utf-8')
    contract_root_path = config.get(BASE_INFO, 'contract_root_path')
    contract_path = config.get(BASE_INFO, 'contract_path')
    contract_name = config.get(BASE_INFO, 'contract_name')   

    os.chdir(contract_root_path)
    sli = Slither(contract_path)
    cs = sli.get_contract_from_name(contract_name)
    assert len(cs) == 1
    c = cs[0]

    if config.has_section(CALL_GRAPH) and config.getboolean(CALL_GRAPH, OPEN):
        call_graph(config, c)
    
    if config.has_section(EXTERNAL_CALL) and config.getboolean(EXTERNAL_CALL, OPEN):
        external_call(config, c)

