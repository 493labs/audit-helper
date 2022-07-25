from configparser import ConfigParser
from enum import Enum, unique
import os

@unique
class Chain(Enum):
    def __new__(cls, url:str, code_url:str, index:int):
        obj = object.__new__(cls)
        if index == 1:
            key_file = './conf/key.ini'
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
    XAVA = "https://api.avax.network/ext/bc/C/rpc/", "http://api.snowtrace.io/api", 43114
    # Polygon = "https://polygon-rpc.com/", "http://api.polygonscan.com/api", 137
    Polygon = "https://rpc-mainnet.matic.quiknode.pro", "http://api.polygonscan.com/api", 137
    

@unique
class TokenType(Enum):
    def __new__(cls, dir:str, index:int):
        obj = object.__new__(cls)
        
        obj.dir = dir 
        obj._value_ = index
        return obj
    ERC20 = 'erc20', 1
    ERC721 = 'erc721', 2
    OTHER = 'other', 99
