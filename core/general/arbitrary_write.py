from slither.core.declarations import Contract, SolidityVariableComposed

def check_arbitrary_write(c: Contract):
    for f in c.functions_entry_points:
        if f.is_constructor:
            continue
        all_state_variables_read = f.all_state_variables_read()
        all_solidity_variables_read = f.all_solidity_variables_read()
        all_state_variables_written = f.all_state_variables_written()
        if len(all_state_variables_read)==0 and \
            SolidityVariableComposed("msg.sender") not in all_solidity_variables_read and \
                len(all_state_variables_written) > 0:
            print(f'{c.name} 合约的 {f.name} 方法存在任意写入风险')
