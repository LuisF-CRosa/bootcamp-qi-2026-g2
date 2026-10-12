import uuid

import pytest
from sqlalchemy import text

from src.models.account import Account, AccountType
from src.repositories.transaction_repository import TransactionRepository
from src.errors.custom_errors import InsufficientBalance, AccountNotFound


def test_database_connection(db):
    """Testa se a conexão com o PostgreSQL está funcionando."""
    result = db.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_create_and_query_account(db):
    """Testa a criação e persistência de uma conta no SQLAlchemy."""
    acc_key = str(uuid.uuid4())
    unique = uuid.uuid4().hex

    personal_type = (
        db.query(AccountType)
        .filter_by(enumerator="PERSONAL")
        .first()
    )

    assert personal_type is not None

    account = Account(
        account_key=acc_key,
        name="Cliente Teste",
        document_number=unique[:14],
        email=f"{unique}@teste.com",
        account_type_id=personal_type.id,
        balance=5000,
    )

    db.add(account)
    db.commit()

    saved_account = (
        db.query(Account)
        .filter_by(account_key=acc_key)
        .first()
    )

    assert saved_account is not None
    assert saved_account.account_key == acc_key
    assert saved_account.name == "Cliente Teste"
    assert saved_account.balance == 5000
    assert saved_account.account_type.enumerator == "PERSONAL"


def test_transfer_success(db, create_accounts):
    """Testa transferência com saldo suficiente e taxa de emergência."""
    repo = TransactionRepository(db)
    accounts = create_accounts

    transaction = repo.execute_transfer(
        source_key=accounts["source"].account_key,
        dest_key=accounts["destination"].account_key,
        amount=5000,
        idempotency_key=str(uuid.uuid4()),
    )

    db.commit()

    db.refresh(accounts["source"])
    db.refresh(accounts["destination"])
    db.refresh(accounts["emergency"])

    assert accounts["source"].balance == 5000
    assert accounts["destination"].balance == 6750
    assert accounts["emergency"].balance == 250

    assert transaction.gross_amount == 5000
    assert transaction.fee_amount == 250
    assert transaction.net_amount == 4750

    assert transaction.source_account_id == accounts["source"].id
    assert transaction.destination_account_id == accounts["destination"].id
    assert transaction.emergency_account_id == accounts["emergency"].id


def test_transfer_insufficient_balance(db, create_accounts):
    """Testa erro quando a origem não possui saldo suficiente."""
    repo = TransactionRepository(db)
    accounts = create_accounts

    source_before = accounts["source"].balance
    destination_before = accounts["destination"].balance
    emergency_before = accounts["emergency"].balance

    with pytest.raises(InsufficientBalance):
        repo.execute_transfer(
            source_key=accounts["source"].account_key,
            dest_key=accounts["destination"].account_key,
            amount=20000,
            idempotency_key=str(uuid.uuid4()),
        )

    db.rollback()

    db.refresh(accounts["source"])
    db.refresh(accounts["destination"])
    db.refresh(accounts["emergency"])

    assert accounts["source"].balance == source_before
    assert accounts["destination"].balance == destination_before
    assert accounts["emergency"].balance == emergency_before


def test_transfer_account_not_found(db, create_accounts):
    """Testa erro ao transferir para uma conta inexistente."""
    repo = TransactionRepository(db)
    accounts = create_accounts

    with pytest.raises(AccountNotFound):
        repo.execute_transfer(
            source_key=accounts["source"].account_key,
            dest_key="00000000-0000-0000-0000-000000000000",
            amount=1000,
            idempotency_key=str(uuid.uuid4()),
        )

    db.rollback()
