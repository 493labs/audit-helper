from configparser import ConfigParser
import json
import os
import requests
from core.utils.url import Chain
from core.utils.change_solc_version import change_solc_version
from slither import Slither
from slither.core.declarations import Contract

def get_contract_creation(chain:Chain, contract_address:str):
    ret = requests.get(chain.code_url, {
        "module": "contract",
        "action": "getcontractcreation",
        "contractaddresses": contract_address,
        "apiKey": ""
    })
    ret_json = ret.json()
    assert ret_json['status']=="1", f'在链{chain}上未找到{contract_address}的创建合约交易'
    result = ret_json['result'][0]
    contractCreator = result['contractCreator']
    txHash = result['txHash']
    return contractCreator, txHash

def get_logs(chain:Chain, contract_address:str, topic0:str, fromBlock = 0, toBlock = 'latest'):
    ret = requests.get(chain.code_url, {
        "module": "logs",
        "action": "getLogs",
        "fromBlock": fromBlock,
        "toBlock": toBlock,
        "address": contract_address,
        "topic0": topic0
    })
    logs = ret.json()['result']
    return logs

class SourceCode:
    def __init__(self, chain: Chain, addr: str, code_dir: str) -> None:
        self.chain = chain
        self.addr = addr
        self.code_dir = code_dir
        self.conf_path = code_dir + '/check.ini'

    def download(self):
        if os.path.exists(self.conf_path):
            return        

        assert self.chain.code_url != "", "the code_url of {} is not set".format(self.chain.name)
        ret = requests.get(self.chain.code_url, {
            "module": "contract",
            "action": "getsourcecode",
            "address": self.addr,
            "apiKey": ""
        })    
        ret_json = ret.json()
        assert ret_json['status']=="1", f'链{self.chain}上未找到{self.addr}的代码'
        # 放在这里避免建立无效目录
        if not os.path.exists(self.code_dir):
            os.makedirs(self.code_dir)
            
        raw_contract_info = ret_json['result'][0]
        raw_source_info: str = raw_contract_info['SourceCode']
        contract_name: str = raw_contract_info['ContractName']
        contract_file_name: str = contract_name + '.sol'

        conf = ConfigParser()
        conf.add_section('info')
        conf.set('info','chain', self.chain.name)
        conf.set('info','address',self.addr)
        conf.set('info','code_path',self.code_dir)
        conf.set('info','contract_name', contract_name)

        if raw_source_info.startswith('{'):
            if raw_source_info.startswith('{{'):
                raw_source_info = raw_source_info[1:-1]
            mul_source_info = json.loads(raw_source_info)
            if 'sources' in mul_source_info:
                mul_source_info = mul_source_info['sources']

            conf.set('info','contract_path', self.get_file_pos_by_contract_name(mul_source_info,contract_name))

            for contract_path, source_info in mul_source_info.items():
                full_file_name = self.code_dir+'/'+contract_path

                temp_dir_path, _ = os.path.split(full_file_name)
                if not os.path.exists(temp_dir_path):
                    os.makedirs(temp_dir_path)
                    
                self.write_sol(full_file_name, source_info['content'])
        else:
            conf.set('info', 'contract_path', contract_file_name)
            self.write_sol(self.code_dir+'/'+contract_file_name, raw_source_info)

        with open(self.conf_path, 'w', encoding='utf-8') as fp:
            conf.write(fp)

    def get_file_pos_by_contract_name(self,mul_source_info,contract_name:str)->str:
        for contract_path in mul_source_info.keys():
            if contract_name in contract_path:
                if contract_path.startswith('/'):
                    # 有些下载path前面有个'/'，比如 ETH 0x0ca0296387687d670d56214b312b19f082b21923
                    return contract_path[1:]
                return contract_path
        # 处理文件名与合约名不一致的情况
        for contract_path, source_info in mul_source_info.items():
            source_content:str = source_info['content']
            for line in source_content.splitlines():
                line = line.lstrip()
                if line.startswith('contract'):
                    line = line[8:].lstrip()
                    if line.startswith(contract_name):
                        return contract_path
        return ''


    def write_sol(self, file_path:str, content:str):
        with open(file_path,'w',encoding='utf-8') as fp:
            # replace用于处理苹果系统上编辑的sol文件到window上的换两行问题
            fp.write(content.replace('\r\n','\n') + "\n\n")
                 

    def get_sli_c_by_conf(self)->Contract:
        if not os.path.exists(self.conf_path):
            self.download()
        check_conf = ConfigParser()
        check_conf.read(self.conf_path,'utf-8')
        contract_path = check_conf.get('info','contract_path')
        contract_name = check_conf.get('info','contract_name')
        return self.get_sli_c(contract_path, contract_name)        

    def get_sli_c(self, contract_path:str, contract_name:str)->Contract:
        raw_dir = os.getcwd()
        os.chdir(self.code_dir) 
        change_solc_version(contract_path)
        sli = Slither(contract_path)
        os.chdir(raw_dir)        
        
        cs = sli.get_contract_from_name(contract_name)
        assert len(cs) == 1, f'找到 {len(cs)} 个名字为 {contract_name} 的合约'
        return cs[0]


def download(chain: Chain, addr: str, token_type: str = None, token_name: str = None):
    if token_type and token_name:
        code_dir = f'sols/{token_type}/' + '_'.join([token_name, chain.name.lower(), addr[-8:].lower()])
    else:
        code_dir = f'sols/raw/' + '_'.join([chain.name.lower(), addr[-8:].lower()])
    source_code = SourceCode(chain, addr, code_dir)
    source_code.download()

def get_sli_c_by_token_info(chain: Chain, addr: str, token_type: str, token_name: str) -> Contract:
    code_dir = f'sols/{token_type}/' + '_'.join([token_name, chain.name.lower(), addr[-8:].lower()])
    source_code = SourceCode(chain, addr, code_dir)
    return source_code.get_sli_c_by_conf()

def get_sli_c_by_addr(chain: Chain, addr: str) -> Contract:
    code_dir = f'sols/raw/' + '_'.join([chain.name.lower(), addr[-8:].lower()])
    source_code = SourceCode(chain, addr, code_dir)
    return source_code.get_sli_c_by_conf()

def get_sli_c(code_dir:str, contract_path:str, contract_name:str) -> Contract:
    source_code = SourceCode(None, None, code_dir)
    return source_code.get_sli_c(contract_path, contract_name)
