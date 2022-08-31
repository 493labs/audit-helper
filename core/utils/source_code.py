from configparser import ConfigParser
import json
import os
import requests
from core.common.e import Chain, TokenType

class SourceCode:

    def __init__(self, chain: Chain, addr: str, token_type: TokenType, token_name: str) -> None:
        self.chain = chain
        self.addr = addr
        self.token_name = token_name
        self.code_path = f'sols/{token_type.dir}/' + '_'.join([token_name, chain.name.lower(), addr[-8:].lower()])
        self.conf_path = self.code_path + './check.ini'

    def download(self):
        if os.path.exists(self.conf_path):
            return
        if not os.path.exists(self.code_path):
            os.makedirs(self.code_path)

        assert self.chain.code_url != "", "the code_url of {} is not set".format(self.chain.name)
        ret = requests.get(self.chain.code_url, {
            "module": "contract",
            "action": "getsourcecode",
            "address": self.addr,
            "apiKey": ""
        })        
        raw_contract_info = ret.json()['result'][0]
        raw_source_info: str = raw_contract_info['SourceCode']
        contract_name: str = raw_contract_info['ContractName']
        contract_file_name: str = contract_name + '.sol'

        conf = ConfigParser()
        conf.add_section('info')
        conf.set('info','chain', self.chain.name)
        conf.set('info','address',self.addr)
        conf.set('info','code_path',self.code_path)
        conf.set('info','contract_name', contract_name)

        if raw_source_info.startswith('{'):
            if raw_source_info.startswith('{{'):
                raw_source_info = raw_source_info[1:-1]
            mul_source_info = json.loads(raw_source_info)
            if 'sources' in mul_source_info:
                mul_source_info = mul_source_info['sources']

            conf.set('info','contract_path', self.get_file_pos_by_contract_name(mul_source_info,contract_name))

            for contract_path, source_info in mul_source_info.items():
                full_file_name = self.code_path+'/'+contract_path

                temp_dir_path, _ = os.path.split(full_file_name)
                if not os.path.exists(temp_dir_path):
                    os.makedirs(temp_dir_path)
                    
                self.write_sol(full_file_name, source_info['content'])
        else:
            conf.set('info', 'contract_path', contract_file_name)
            self.write_sol(self.code_path+'/'+contract_file_name, raw_source_info)

        with open(self.conf_path, 'w', encoding='utf-8') as fp:
            conf.write(fp)

    def get_file_pos_by_contract_name(self,mul_source_info,contract_name:str)->str:
        for contract_path in mul_source_info.keys():
            if contract_name in contract_path:
                return contract_path
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
            
    def get_code_path(self) -> str:
        return self.code_path
