from slither.core.declarations import Contract, Function, SolidityVariableComposed
from slither.core.cfg.node import NodeType
from core.frame.base_node import DecisionNode, NodeReturn
from core.frame.contract_info import ContractInfo

class AuthenticationNode(DecisionNode):

    def check(self, contract_info: ContractInfo) -> NodeReturn:
        unusualAuthenticationFnames = []
        for f in contract_info.c.functions_entry_points:
            if f.is_constructor:
                continue
            all_state_variables_read = f.all_state_variables_read()
            all_solidity_variables_read = f.all_solidity_variables_read()
            all_state_variables_written = f.all_state_variables_written()

            if len(all_state_variables_read)==0 and \
                  SolidityVariableComposed("msg.sender") not in all_solidity_variables_read and \
                    len(all_state_variables_written) > 0:
                unusualAuthenticationFnames.append(f.name)
                # print(f'{.c.name} 合约的 {f.name} 方法存在任意写入风险')
                continue

            if len(all_state_variables_written) > 0 and \
              not self.has_msg_sendor_authentication(f) and not self.has_initialization_mechanism(f):
                # print(f'{c.name} 合约的 {f.name} 方法未进行鉴权或未正确的初始化')
                unusualAuthenticationFnames.append(f.name)

        if len(unusualAuthenticationFnames) == 0:
            self.add_info('未发现直接调用sstore和delegatecall的情况')
        else:
            fnames = ','.join(unusualAuthenticationFnames)
            self.add_warn(f'{fnames}存在权限异常情况')
        return NodeReturn.branch0


    # 是否具有msg.sendor鉴权
    def has_msg_sendor_authentication(self, f: Function) -> bool:
        all_conditional_solidity_variables_read = f.all_conditional_solidity_variables_read()
        if SolidityVariableComposed("msg.sender") in all_conditional_solidity_variables_read:
            return True
        
        # 基于`_msgSender()`方法返回`msg.sendor`的情况
        for ff in f.all_internal_calls():
            if ff.name == '_msgSender':
                self.add_focus(f'{f.name} 中存在`_msgSender()`，需要人工判断`msg.sendor`的鉴权情况')
                return True
        
        # 基于将`msg.sendor`赋予临时变量的情况
        for node in f.nodes:
            if node.type == NodeType.VARIABLE:
                if SolidityVariableComposed("msg.sender") in node.solidity_variables_read:
                    self.add_focus(f'{f.name} 中存在 {node.expression} ，需要人工判断`msg.sendor`的鉴权情况')
                    return True
        return False

    # 是否具有初始化机制
    def has_initialization_mechanism(self, f: Function) -> bool:
        for m in f.modifiers:
            if m.name == 'initializer':
                return True
        return False

           
