from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, CHAR
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import Base

class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(BigInteger, primary_key=True)
    transaction_key = Column(CHAR(36), nullable=False, unique=True)
    source_account_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    destination_account_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    emergency_account_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    gross_amount = Column(BigInteger, nullable=False)
    fee_amount = Column(BigInteger, nullable=False, default=0)
    net_amount = Column(BigInteger, nullable=False)
    idempotency_key = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class TransactionEvent(Base):
    __tablename__ = "transaction_event"

    id = Column(BigInteger, primary_key=True)
    transaction_id = Column(BigInteger, ForeignKey("transaction.id"), nullable=False)
    status = Column(String(50), nullable=False)
    event_datetime = Column(DateTime, default=datetime.utcnow, nullable=False)