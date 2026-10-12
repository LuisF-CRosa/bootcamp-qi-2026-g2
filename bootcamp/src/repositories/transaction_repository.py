from uuid import uuid4

from sqlalchemy.orm import Session

from src.models.account import Account
from src.models.transaction import Transaction, TransactionEvent
from src.errors.custom_errors import InsufficientBalance, AccountNotFound


class TransactionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_account_for_update(self, account_key: str) -> Account:
        """
        Busca uma conta aplicando trava explícita de linha FOR UPDATE.
        """
        account = (
            self.session.query(Account)
            .filter(Account.account_key == account_key)
            .with_for_update()
            .first()
        )

        if not account:
            raise AccountNotFound(
                f"Conta com chave {account_key} não encontrada."
            )

        return account

    def get_emergency_account_for_update(self) -> Account:
        """
        Busca a conta do Fundo de Emergência aplicando trava.
        """
        account = (
            self.session.query(Account)
            .filter(
                Account.account_type.has(
                    enumerator="EMERGENCY"
                )
            )
            .with_for_update()
            .first()
        )

        return account

    def check_idempotency(
        self,
        idempotency_key: str,
    ) -> Transaction:
        """
        Verifica se já existe uma transação com a mesma
        chave de idempotência.
        """
        if idempotency_key:
            return (
                self.session.query(Transaction)
                .filter(
                    Transaction.idempotency_key
                    == idempotency_key
                )
                .first()
            )

        return None

    def execute_transfer(
        self,
        source_key: str,
        dest_key: str,
        amount: int,
        fee_rate: float = 0.05,
        idempotency_key: str = None,
    ) -> Transaction:
        """
        Executa uma transferência entre contas,
        destinando parte do valor ao Fundo de Emergência.
        """

        # Verificação de idempotência
        existing_tx = self.check_idempotency(
            idempotency_key
        )

        if existing_tx:
            return existing_tx

        # Busca e trava as contas
        source_acc = self.get_account_for_update(
            source_key
        )

        dest_acc = self.get_account_for_update(
            dest_key
        )

        emergency_acc = (
            self.get_emergency_account_for_update()
        )

        # Verificação de saldo
        if source_acc.balance < amount:
            raise InsufficientBalance(
                "Saldo insuficiente para realizar "
                "a transferência."
            )

        # Cálculo da tarifa
        fee_amount = int(amount * fee_rate)
        net_amount = amount - fee_amount

        # Atualização dos saldos
        source_acc.balance -= amount

        dest_acc.balance += net_amount

        if emergency_acc:
            emergency_acc.balance += fee_amount

        # Registro da transação
        tx = Transaction(
            transaction_key=str(uuid4()),
            source_account_id=source_acc.id,
            destination_account_id=dest_acc.id,
            emergency_account_id=(
                emergency_acc.id
                if emergency_acc
                else None
            ),
            gross_amount=amount,
            fee_amount=fee_amount,
            net_amount=net_amount,
            idempotency_key=idempotency_key,
        )

        self.session.add(tx)
        self.session.flush()

        # Registro do evento de sucesso
        tx_event = TransactionEvent(
            transaction_id=tx.id,
            status="SUCCESS",
        )

        self.session.add(tx_event)

        return tx
