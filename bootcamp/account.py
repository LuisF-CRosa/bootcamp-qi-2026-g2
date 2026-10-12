from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, CHAR
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import Base


class AccountType(Base):
    __tablename__ = "account_type"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False, unique=True)


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True)
    account_key = Column(CHAR(36), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    document_number = Column(String(14), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    account_type_id = Column(Integer, ForeignKey(
        "account_type.id"), nullable=False)
    balance = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    account_type = relationship("AccountType", lazy="selectin")
