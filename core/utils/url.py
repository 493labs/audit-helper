from configparser import ConfigParser
from enum import Enum, unique
import os

@unique
class Chain(Enum):
    def __new__(cls, url:str, code_url:str, index:int):
        obj = object.__new__(cls)
        if index in (1, 5):
            key_file = os.getcwd() + '/config/key.ini'
            if os.path.exists(key_file):
                key_conf = ConfigParser()
                key_conf.read(key_file,encoding='utf-8')
                url = url + key_conf.get('key','infura_key')
        obj.url = url      
        obj.code_url = code_url
        obj._value_ = index
        return obj
    Eth = "https://mainnet.infura.io/v3/", "http://api.etherscan.io/api", 1
    Bsc = "https://bsc-dataseed.binance.org/", "http://api.bscscan.com/api", 56
    XAVA = "https://ava-mainnet.public.blastapi.io/ext/bc/C/rpc", "http://api.snowtrace.io/api", 43114
    Polygon = "https://rpc-mainnet.matic.quiknode.pro", "http://api.polygonscan.com/api", 137
    # CHZ 无法读取链上slot  https://explorer.chiliz.com/eth-rpc-api-docs
    CHZ = "https://explorer.chiliz.com/api/eth-rpc", "http://explorer.chiliz.com/api", 999
    # https://docs.step.network/step-network/networks
    STEP = "https://rpc.step.network", "http://stepscan.io/api", 1234
    ArbitrumOne = "https://arb1.arbitrum.io/rpc","http://api.arbiscan.io/api", 42161
    Goerli = "https://goerli.infura.io/v3/", "http://api-goerli.etherscan.io/api", 5
    Mantle = "https://rpc.mantle.xyz", "https://explorer.mantle.xyz/api", 5000
    Optimistic = "https://mainnet.optimism.io", "https://api-optimistic.etherscan.io/api", 10
    