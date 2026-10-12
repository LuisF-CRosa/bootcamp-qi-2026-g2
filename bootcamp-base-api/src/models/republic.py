"""Mapeamento SQLAlchemy das tabelas da republica em database/database.sql.

O SQL de inicializacao cria as tabelas. Estes modelos permitem que os
repositories usem a mesma estrutura sem misturar SQL com regras de negocio.
"""

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    CHAR,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from models.base import Base


class Client(Base):
    __tablename__ = "client"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_key = Column(CHAR(36), nullable=False, unique=True)
    client_type = Column(String(30), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    document_number = Column(CHAR(14), unique=True)
    birthdate = Column(Date)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "client_type IN ('PERSONAL_CLIENT', 'INSTITUTIONAL_CLIENT')",
            name="client_type_valid",
        ),
        CheckConstraint(
            "(client_type = 'PERSONAL_CLIENT' AND document_number IS NOT NULL "
            "AND birthdate IS NOT NULL) OR "
            "(client_type = 'INSTITUTIONAL_CLIENT' AND document_number IS NULL "
            "AND birthdate IS NULL)",
            name="client_documents_by_type",
        ),
        CheckConstraint("LENGTH(TRIM(name)) > 0", name="client_name_not_blank"),
        CheckConstraint("LENGTH(TRIM(email)) > 0", name="client_email_not_blank"),
        Index(
            "one_institutional_client",
            "client_type",
            unique=True,
            postgresql_where=text("client_type = 'INSTITUTIONAL_CLIENT'"),
        ),
    )

    accounts = relationship("Account", back_populates="client")


class AccountStatus(Base):
    __tablename__ = "account_status"

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    enumerator = Column(String(30), nullable=False, unique=True)


class Account(Base):
    __tablename__ = "account"

    PERSONAL = "PERSONAL"
    HOUSE = "HOUSE"
    EMERGENCY = "EMERGENCY"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_key = Column(CHAR(36), nullable=False, unique=True)
    client_id = Column(BigInteger, ForeignKey("client.id"), nullable=False)
    account_type = Column(String(20), nullable=False)
    status_id = Column(SmallInteger, ForeignKey("account_status.id"), nullable=False)
    balance_cents = Column(BigInteger, nullable=False, server_default=text("0"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "account_type IN ('PERSONAL', 'HOUSE', 'EMERGENCY')",
            name="account_type_valid",
        ),
        CheckConstraint("balance_cents >= 0", name="account_balance_nonnegative"),
        Index(
            "one_active_account_per_type",
            "client_id",
            "account_type",
            unique=True,
            postgresql_where=text("status_id = 1"),
        ),
        Index("account_by_client", "client_id", "id"),
    )

    client = relationship("Client", back_populates="accounts")
    status = relationship("AccountStatus")
    status_events = relationship(
        "AccountStatusEvent", back_populates="account", order_by="AccountStatusEvent.id"
    )
    entries = relationship("AccountEntry", back_populates="account")


class AccountStatusEvent(Base):
    __tablename__ = "account_status_event"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(BigInteger, ForeignKey("account.id"), nullable=False)
    status_id = Column(SmallInteger, ForeignKey("account_status.id"), nullable=False)
    event_datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reason = Column(String(255))

    __table_args__ = (
        Index("account_status_event_history", "account_id", "event_datetime", "id"),
    )

    account = relationship("Account", back_populates="status_events")
    status = relationship("AccountStatus")


class TransactionStatus(Base):
    __tablename__ = "transaction_status"

    CREATED = "CREATED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    enumerator = Column(String(30), nullable=False, unique=True)


class FinancialTransaction(Base):
    __tablename__ = "financial_transaction"

    SIMULATED_DEPOSIT = "SIMULATED_DEPOSIT"
    TRANSFER = "TRANSFER"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_key = Column(CHAR(36), nullable=False, unique=True)
    operation_type = Column(String(30), nullable=False)
    source_account_id = Column(BigInteger, ForeignKey("account.id"))
    destination_account_id = Column(BigInteger, ForeignKey("account.id"), nullable=False)
    gross_amount_cents = Column(BigInteger, nullable=False)
    fee_amount_cents = Column(BigInteger, nullable=False, server_default=text("0"))
    idempotency_key = Column(String(255), nullable=False, unique=True)
    request_fingerprint = Column(CHAR(64), nullable=False)
    status_id = Column(SmallInteger, ForeignKey("transaction_status.id"), nullable=False)
    response_status = Column(SmallInteger)
    response_body = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "operation_type IN ('SIMULATED_DEPOSIT', 'TRANSFER')",
            name="transaction_type_valid",
        ),
        CheckConstraint("gross_amount_cents > 0", name="transaction_amount_positive"),
        CheckConstraint(
            "fee_amount_cents >= 0 AND fee_amount_cents <= gross_amount_cents",
            name="transaction_fee_valid",
        ),
        CheckConstraint(
            "(operation_type = 'SIMULATED_DEPOSIT' AND source_account_id IS NULL "
            "AND fee_amount_cents = 0) OR "
            "(operation_type = 'TRANSFER' AND source_account_id IS NOT NULL "
            "AND source_account_id <> destination_account_id)",
            name="transaction_accounts_valid",
        ),
        CheckConstraint(
            "(response_status IS NULL AND response_body IS NULL) OR "
            "(response_status IS NOT NULL AND response_body IS NOT NULL)",
            name="transaction_response_together",
        ),
    )

    source_account = relationship("Account", foreign_keys=[source_account_id])
    destination_account = relationship("Account", foreign_keys=[destination_account_id])
    status = relationship("TransactionStatus")
    status_events = relationship(
        "TransactionStatusEvent",
        back_populates="transaction",
        order_by="TransactionStatusEvent.id",
    )
    entries = relationship("AccountEntry", back_populates="transaction")


class TransactionStatusEvent(Base):
    __tablename__ = "transaction_status_event"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id = Column(
        BigInteger, ForeignKey("financial_transaction.id"), nullable=False
    )
    status_id = Column(SmallInteger, ForeignKey("transaction_status.id"), nullable=False)
    event_datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index(
            "transaction_status_event_history", "transaction_id", "event_datetime", "id"
        ),
    )

    transaction = relationship("FinancialTransaction", back_populates="status_events")
    status = relationship("TransactionStatus")


class AccountEntry(Base):
    __tablename__ = "account_entry"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id = Column(
        BigInteger, ForeignKey("financial_transaction.id"), nullable=False
    )
    account_id = Column(BigInteger, ForeignKey("account.id"), nullable=False)
    signed_amount_cents = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("signed_amount_cents <> 0", name="account_entry_nonzero"),
        Index(
            "account_entry_statement",
            "account_id",
            created_at.desc(),
            id.desc(),
        ),
    )

    transaction = relationship("FinancialTransaction", back_populates="entries")
    account = relationship("Account", back_populates="entries")
