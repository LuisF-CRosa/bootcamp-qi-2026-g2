class AccountNotFound(Exception):
    def __init__(self, message="Conta não encontrada"):
        self.message = message
        super().__init__(self.message)

class InsufficientBalance(Exception):
    def __init__(self, message="Saldo insuficiente"):
        self.message = message
        super().__init__(self.message)

class DuplicateTransaction(Exception):
    def __init__(self, message="Transação duplicada"):
        self.message = message
        super().__init__(self.message)
