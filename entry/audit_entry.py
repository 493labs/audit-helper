from configparser import ConfigParser
import os
from slither import Slither
from slither.core.declarations import Contract
import sys
sys.path.append('.')
from core.visualize.call_graph import CallGraph, View
from core.general.analyze_frame import general_analyze
from core.utils.change_solc_version import change_solc_version

AUDIT_HELPER = 'audit-helper'

def call_graph(config:ConfigParser, c:Contract):  
    analyze = CallGraph(c)
    if config.getboolean(AUDIT_HELPER, 'global_call_graph'):
        analyze.generate_graph(View.In_Call)
        analyze.generate_graph(View.Ex_Call)
        analyze.generate_graph(View.All_Call)
    if config.getboolean(AUDIT_HELPER, 'function_call_graph'):
        for fname in config.get(AUDIT_HELPER, 'function_names').split(','):
            fname = fname.strip()
            analyze.generate_graph(View.All_Call, True, fname)
    if config.getboolean(AUDIT_HELPER, 'write_read_graph'):
        analyze.gene_wt_graph()

def audit_helper(config:ConfigParser):
    root_path = config.get(AUDIT_HELPER, 'root_path')
    contract_path = config.get(AUDIT_HELPER, 'contract_path')
    contract_name = config.get(AUDIT_HELPER, 'contract_name')   

    os.chdir(root_path)
    change_solc_version(contract_path)
    sli = Slither(contract_path)
    cs = sli.get_contract_from_name(contract_name)
    assert len(cs) == 1
    c = cs[0]

    if config.getboolean(AUDIT_HELPER, 'with_call_graph'):
        call_graph(config, c)

    if config.getboolean(AUDIT_HELPER, 'with_general_check'):
        layerouts = general_analyze(c=c)
        for layerout in layerouts:
            print(layerout)



if __name__ == "__main__":
    config = ConfigParser()    
    config.read(os.path.dirname(__file__) + '/audit.ini', 'utf-8')
    audit_helper(config) 

