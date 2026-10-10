from sqlalchemy.orm import Session
from src.repositories.transaction_repository import TransactionRepository
from src.dtos.transaction_dto import TransactionDTO

class TransactionController:
    def __init__(self, session: Session):
        self.session = session
        self.repository = TransactionRepository(session)

    def transfer(self, payload: dict, idempotency_key: str) -> dict:
        source_key = payload["source_account_key"]
        dest_key = payload["destination_account_key"]
        amount = payload["amount"]

        # Executa operação dentro da transação ACID do repositório
        tx = self.repository.execute_transfer(
            source_key=source_key,
            dest_key=dest_key,
            amount=amount,
            idempotency_key=idempotency_key
        )

        # Confirmar alterações no banco
        self.session.commit()

        return TransactionDTO.to_dict(tx)