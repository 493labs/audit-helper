from configparser import ConfigParser
import json
import os
import requests
from .e import Chain

INFO = 'info'

class SourceCode:

    def __init__(self, chain: Chain, addr: str, token_name: str) -> None:
        self.chain = chain
        self.addr = addr
        self.token_name = token_name
        self.code_path = 'sols/erc/' + '_'.join([token_name, chain.name.lower(), addr[-8:].lower()])

    def download(self):
        if os.path.exists(self.code_path):
            return
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
        contract_file_name: str = raw_contract_info['ContractName'] + '.sol'

        conf = ConfigParser()
        conf.add_section('info')
        conf.set('info','chain', self.chain.name)
        conf.set('info','address',self.addr)
        conf.set('info','code_path',self.code_path)

        if raw_source_info.startswith('{'):
            if raw_source_info.startswith('{{'):
                raw_source_info = raw_source_info[1:-1]
            mul_source_info = json.loads(raw_source_info)
            if 'sources' in mul_source_info:
                mul_source_info = mul_source_info['sources']

            for contract_path, source_info in mul_source_info.items():
                if contract_path.endswith(contract_file_name):
                    conf.set(INFO, 'contract_path', contract_path)
                full_file_name = self.code_path+'/'+contract_path

                temp_dir_path, _ = os.path.split(full_file_name)
                if not os.path.exists(temp_dir_path):
                    os.makedirs(temp_dir_path)
                    
                with open(full_file_name, 'w') as fp:
                    fp.write(source_info['content'] + "\n\n")
        else:
            conf.set(INFO, 'contract_path', contract_file_name)
            with open(self.code_path+'/'+contract_file_name, 'w') as fp:
                fp.write(raw_source_info + "\n\n")

        with open(self.code_path + '/check.ini', 'w') as fp:
            conf.write(fp)
            

    def get_code_path(self) -> str:
        return self.code_path
