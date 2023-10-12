from configparser import ConfigParser
import os
from typing import List
from slither import Slither
from slither.core.declarations import Contract
import sys
sys.path.append('.')
from core.visualize.call_graph import CallGraph, View
from core.general.analyze_frame import general_analyze
from core.utils.change_solc_version import change_solc_version
from core.general.base_node import rank_layerouts

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

# 获取指定目录中所有sol文件（不包含子目录中的）未被继承的合约
def get_contracts(contracts_dir:str)->List[Contract]:
    has_change_solc_version = False
    global_derived_contracts:List[Contract] = []
    global_inheritance_names = []
    for file in os.listdir(contracts_dir):
        if os.path.isfile(file) and file.endswith('.sol'):
            path = f'{contracts_dir}/{file}'
            if not has_change_solc_version:
                change_solc_version(path)
                has_change_solc_version = True
            sli = Slither(path)
            cur_derived_contracts = [c for c in sli.contracts_derived if c.contract_kind == "contract"]
            cur_inheritance_names = [c.name for c in sli.contracts if c.contract_kind == "contract" and c not in cur_derived_contracts]

            # 从global_derived_contracts中删除cur_inheritance_names包含的内容
            to_remove = []
            for c in global_derived_contracts:
                if c.name in cur_inheritance_names:
                    to_remove.append(c)
            for c in to_remove:
                global_derived_contracts.remove(c)

            # 从cur_derived_contracts中去掉global_inheritance_names中包含的，然后加到global_derived_contracts中
            for c in cur_derived_contracts:
                if c.name not in global_inheritance_names:
                    global_derived_contracts.append(c)
            
            # 往global_inheritance_names中加上cur_inheritance_names包含的内容
            for name in cur_inheritance_names:
                if name not in global_inheritance_names:
                    global_inheritance_names.append(name)

    global_derived_contract_names = [c.name for c in global_derived_contracts]
    assert len(global_derived_contract_names) == len(set(global_derived_contract_names)), '存在不同文件定义同样合约名的情况'
    return global_derived_contracts

def audit_helper(config:ConfigParser):
    root_path = config.get(AUDIT_HELPER, 'root_path')
    os.chdir(root_path)

    has_multi_contracts = config.getboolean(AUDIT_HELPER, 'has_multi_contracts')
    if has_multi_contracts:
        contracts_dir = config.get(AUDIT_HELPER, 'entry_dir')
        cs = get_contracts(contracts_dir)
    else:
        entry_file = config.get(AUDIT_HELPER, 'entry_file')
        entry_contract = config.get(AUDIT_HELPER, 'entry_contract')   

        change_solc_version(entry_file)
        sli = Slither(entry_file)
        cs = sli.get_contract_from_name(entry_contract)
        assert len(cs) == 1

    #if config.getboolean(AUDIT_HELPER, 'with_call_graph'):
    #    call_graph(config, c)

    if config.getboolean(AUDIT_HELPER, 'with_general_check'):
        for c in cs:
            print(f'-----------------{c.name}-----------------')
            layerouts = general_analyze(c=c)
            for layerout in layerouts:
                print(layerout)
            print('\n\n')

if __name__ == "__main__":
    config = ConfigParser()    
    config.read(os.path.dirname(__file__) + '/audit.ini', 'utf-8')
    audit_helper(config) 

