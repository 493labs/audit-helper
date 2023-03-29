from mythril.disassembler.disassembly import Disassembly
from bytecode.frame.annotation.instruction_trace import get_instruction_trace
from bytecode.support.analyze_result import analyze_use_db, DB_FLAG
from bytecode.frame.svm import SVM

def is_contract_check(disassembly:Disassembly, db_flag:DB_FLAG = DB_FLAG.NoUse, db = None)->bool:
    svm = SVM()
    final_states = svm.exec(disassembly,concrete_storage=False)
    for final_state in final_states:
        insts = get_instruction_trace(final_state)
        if insts:
            for inst in insts:
                if inst['opcode'] in ['EXTCODESIZE', 'EXTCODEHASH']:
                    return True
    return False