from configparser import ConfigParser
import os
from slither import Slither
from slither.core.declarations import Contract
import sys
sys.path.append('.')
from core.visualize.call_graph import CallGraph, View
from core.general.external_call import ExternalCall
from core.common.e import Chain, TokenType
from core.utils.source_code import SourceCode
from core.utils.change_solc_version import change_solc_version
from core.token.check_entry import check_token

AUDIT_HELPER = 'audit-helper'
DOWNLOAD = 'download'
ERC20_CHECK = 'erc20-check'
OPEN = 'open'

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

def external_call(config:ConfigParser, c:Contract):
    ex_call_analyze = ExternalCall(c)
    ex_call_analyze.find_dangerous_ex_call()

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

    if config.getboolean(AUDIT_HELPER, 'with_external_call_check'):
        external_call(config, c)


def _check_token(code_path:str):
    check_conf_path = code_path + '/check.ini'
    assert os.path.exists(check_conf_path), '请先下载代码'
    token_conf = ConfigParser()
    token_conf.read(check_conf_path, 'utf-8')
    os.chdir(code_path)
    contract_path = token_conf.get('info', 'contract_path')
    change_solc_version(contract_path)
    sli = Slither(contract_path)
    for c in sli.contracts_derived:
        if c.kind!="contract":
            continue
        check_token(c)

def download(config: ConfigParser):
    chain_id = config.getint(DOWNLOAD,'chain_id')
    for e in Chain._member_map_.values():
        if chain_id == e.value:
            chain = e
            break
    assert 'chain' in locals(), "暂不支持该链：" + str(chain_id)
    
    token_address = config.get(DOWNLOAD,'token_address')
    token_name = config.get(DOWNLOAD,'token_name')
    token_type_id = config.getint(DOWNLOAD, 'token_type')
    for e in TokenType._member_map_.values():
        if token_type_id == e.value:
            token_type = e
            break
    if 'token_type' not in locals():
        token_type = TokenType.OTHER

    source_code = SourceCode(chain, token_address, token_type, token_name)
    source_code.download()
    if config.getboolean(DOWNLOAD, 'with_token_check'):        
        _check_token(source_code.get_code_path())

def erc20_check(config: ConfigParser):
    _check_token(config.get(ERC20_CHECK, 'code_path'))


if __name__ == "__main__":
    config = ConfigParser()
    config.read('./task.ini', 'utf-8')    

    if config.has_section(AUDIT_HELPER) and config.getboolean(AUDIT_HELPER, OPEN):
        audit_helper(config)

    if config.has_section(DOWNLOAD) and config.getboolean(DOWNLOAD, OPEN):
        download(config)
    
