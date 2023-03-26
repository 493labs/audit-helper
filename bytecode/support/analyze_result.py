from mythril.support.signatures import SQLiteDB, Singleton
import os
from typing import Optional
# import pickle
from eth_utils.crypto import keccak

# class AnalyzeResult:
#     def __init__(self, version:int, data_type:str, data:bytes) -> None:
#         self.version = version
#         self.data_type = data_type
#         self.data = data

#     def dumps(self)->str:
#         return pickle.dumps(self).hex()
    
#     @staticmethod
#     def loads(data:str)->'AnalyzeResult':
#         return pickle.loads(bytes.fromhex(data))

class AnalyzeResultDB(object, metaclass=Singleton):
# class AnalyzeResultDB:

    def __init__(self, path: str = None) -> None:
        if path is None:
            self.path = os.environ.get("MYTHRIL_DIR") or os.path.join(
                os.path.expanduser("~"), ".mythril"
            )
        self.path = os.path.join(self.path, "analyze_result.db")
        with SQLiteDB(self.path) as cur:
            cur.execute(
                (
                    "CREATE TABLE IF NOT EXISTS analyze_result"
                    "(code_hash VARCHAR(66), serialized_data VARCHAR(512),"
                    "PRIMARY KEY (code_hash))"
                )
            )

    def __getitem__(self, item: str) -> Optional[str]:
        """Provide dict interface db[sighash]
        """
        return self.get(code_hash=item)

    @staticmethod
    def _normalize_code_hash(code_hash: str) -> str:
        if not code_hash.startswith("0x"):
            code_hash = "0x" + code_hash
        if not len(code_hash) == 66:
            raise ValueError(
                "Invalid code hash %s, must have 66 characters", code_hash
            )
        return code_hash

    def add(self, code_hash: str, serialized_data: str) -> None:
        code_hash = self._normalize_code_hash(code_hash)
        with SQLiteDB(self.path) as cur:
            # ignore new row if it's already in the DB (and would cause a unique constraint error)
            cur.execute(
                "INSERT OR REPLACE INTO analyze_result (code_hash, serialized_data) VALUES (?,?)",
                (code_hash, serialized_data),
            )

    def get(self, code_hash: str) -> Optional[str]:

        code_hash = self._normalize_code_hash(code_hash)

        with SQLiteDB(self.path) as cur:
            cur.execute("SELECT serialized_data FROM analyze_result WHERE code_hash=?", (code_hash,))
            serialized_data = cur.fetchone()
        if serialized_data:
            return serialized_data[0]
        
    def get_result_from_code_str(self, code:str) -> Optional[str]:
        code_hash = keccak(hexstr=code).hex()
        return self.get(code_hash)
    
    def __repr__(self):
        return f"<AnalyzeResultDB path='{self.path}'>"

from functools import wraps   
import json
from mythril.disassembler.disassembly import Disassembly 
from enum import Enum

class DB_FLAG(Enum):
    NoUse = 0
    Normal = 1
    JustWrite = 2

def analyze_use_db(key:str):
    def inner(func):
        @wraps(func)
        def analyze(*args, **kwargs):
            if 'db_flag' not in kwargs or kwargs['db_flag'] not in [DB_FLAG.Normal, DB_FLAG.JustWrite]:
                return func(*args, **kwargs)
            else:
                if 'db' in kwargs and kwargs['db']:
                    db = kwargs['db']
                else:
                    db = AnalyzeResultDB()
                assert isinstance(args[0], Disassembly)
                code_hash = keccak(hexstr=args[0].bytecode).hex()
                analyze_result_json = db.get(code_hash)
                if analyze_result_json:
                    analyze_result = json.loads(analyze_result_json)
                else:
                    analyze_result = {}

                if kwargs['db_flag'] == DB_FLAG.JustWrite or key not in analyze_result:
                    analyze_result[key] = func(*args, **kwargs)
                    db.add(code_hash, json.dumps(analyze_result))
                return analyze_result[key]
        return analyze
    return inner