from .e import TokenType

class TokenCheckOutput:
    def __init__(self) -> None:
        self.token_type = TokenType.ERC20
        self.close_checks = []
        self.standard_func_checks = []
        self.external_checks = []
        self.overflow_checks = []
        self.fake_recharges = []
        self.token_type = TokenType.ERC20

    def set_token_type(self, token_type:TokenType):
        self.token_type = token_type

    def add_close_check(self, close_check):
        self.close_checks.append(close_check)

    def add_standard_func_check(self, standard_func_check):
        self.standard_func_checks.append(standard_func_check)

    def add_external_check(self, external_check):
        self.external_checks.append(external_check)

    def add_overflow_check(self, overflow_check):
        self.overflow_checks.append(overflow_check)

    def add_fake_recharge(self, fake_recharge):
        self.fake_recharges.append(fake_recharge)

    def get_output(self)->str:
        output = f'此token的类型为{self.token_type}'
        if self.token_type == TokenType.OTHER:
            output = f'此token的类型未知'
            return output
        output += '-----------------check start-----------------\n'
        output += '--------封闭性检查--------\n'
        for close_check in self.close_checks:
            output += close_check + '\n'
        output += '--------标准方法读写检查--------\n'
        for standard_func_check in self.standard_func_checks:
            output += standard_func_check + '\n'
        output += '--------写重要状态的方法外部调用检查--------\n'
        for external_check in self.external_checks:
            output += external_check + '\n'
        output += '--------溢出检查--------\n'
        for overflow_check in self.overflow_checks:
            output += overflow_check + '\n'
        output += '--------假充值检查--------\n'
        for fake_recharge in self.fake_recharges:
            output += fake_recharge + '\n'
        output += '-----------------check end-----------------'
        return output

token_check_output = TokenCheckOutput()
