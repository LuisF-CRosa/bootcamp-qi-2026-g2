import os
import uuid

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)

from src.models.base import Base
from src.models.account import (
    Account,
    AccountType,
)

# Importados para registrar as tabelas
# no metadata do SQLAlchemy
from src.models.transaction import (
    Transaction,
    TransactionEvent,
)


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    (
        "postgresql://postgres:"
        "postgres_password@db_test:5432/"
        "bootcamp_test_db"
    ),
)


test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)


TestSession = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )
)


@pytest.fixture(
    scope="session",
    autouse=True,
)
def setup_database():
    """
    Cria um banco limpo exclusivamente
    para os testes.
    """

    Base.metadata.drop_all(
        bind=test_engine
    )

    Base.metadata.create_all(
        bind=test_engine
    )

    session = TestSession()

    try:
        account_types = [
            "PERSONAL",
            "HOUSE",
            "EMERGENCY",
        ]

        for account_type_name in account_types:
            session.add(
                AccountType(
                    enumerator=account_type_name
                )
            )

        session.commit()

    finally:
        session.close()
        TestSession.remove()

    yield

    Base.metadata.drop_all(
        bind=test_engine
    )


@pytest.fixture
def db():
    """
    Cria uma sessão de banco independente
    para cada teste.
    """

    session = TestSession()

    try:
        yield session

    finally:
        session.rollback()
        session.close()

        TestSession.remove()


@pytest.fixture
def create_accounts(db):
    """
    Cria contas utilizadas nos testes
    de transferência.
    """

    personal_type = (
        db.query(AccountType)
        .filter_by(
            enumerator="PERSONAL"
        )
        .first()
    )

    house_type = (
        db.query(AccountType)
        .filter_by(
            enumerator="HOUSE"
        )
        .first()
    )

    emergency_type = (
        db.query(AccountType)
        .filter_by(
            enumerator="EMERGENCY"
        )
        .first()
    )

    unique1 = uuid.uuid4().hex
    unique2 = uuid.uuid4().hex
    unique3 = uuid.uuid4().hex

    source_account = Account(
        account_key=str(uuid.uuid4()),
        name="Conta Origem Teste",
        document_number=unique1[:14],
        email=f"{unique1}@teste.com",
        account_type_id=personal_type.id,
        balance=10000,
    )

    destination_account = Account(
        account_key=str(uuid.uuid4()),
        name="Conta Destino Teste",
        document_number=unique2[:14],
        email=f"{unique2}@teste.com",
        account_type_id=house_type.id,
        balance=2000,
    )

    emergency_account = Account(
        account_key=str(uuid.uuid4()),
        name="Conta Emergência Teste",
        document_number=unique3[:14],
        email=f"{unique3}@teste.com",
        account_type_id=emergency_type.id,
        balance=0,
    )

    db.add_all(
        [
            source_account,
            destination_account,
            emergency_account,
        ]
    )

    db.commit()

    db.refresh(source_account)
    db.refresh(destination_account)
    db.refresh(emergency_account)

    return {
        "source": source_account,
        "destination": destination_account,
        "emergency": emergency_account,
    }
