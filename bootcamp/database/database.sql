-- Tabela de tipos de conta

CREATE TABLE account_type (
    id SERIAL PRIMARY KEY,
    enumerator VARCHAR(50) NOT NULL UNIQUE
);


-- Tipos de conta do sistema

INSERT INTO account_type (enumerator)
VALUES
    ('PERSONAL'),
    ('HOUSE'),
    ('EMERGENCY');


-- Tabela de contas

CREATE TABLE account (
    id SERIAL PRIMARY KEY,

    account_key CHAR(36) NOT NULL UNIQUE,

    name VARCHAR(255) NOT NULL,

    document_number CHAR(14) NOT NULL UNIQUE,

    email VARCHAR(255) NOT NULL UNIQUE,

    account_type_id INTEGER NOT NULL
        REFERENCES account_type(id),

    balance BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT balance_nao_negativo
        CHECK (balance >= 0)
);


-- Tabela de transações

CREATE TABLE transaction (
    id BIGSERIAL PRIMARY KEY,

    transaction_key CHAR(36) NOT NULL UNIQUE,

    source_account_id INTEGER
        REFERENCES account(id),

    destination_account_id INTEGER
        REFERENCES account(id),

    emergency_account_id INTEGER
        REFERENCES account(id),

    gross_amount BIGINT NOT NULL,

    fee_amount BIGINT NOT NULL DEFAULT 0,

    net_amount BIGINT NOT NULL,

    idempotency_key VARCHAR(255) UNIQUE,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);


-- Histórico de eventos das transações

CREATE TABLE transaction_event (
    id BIGSERIAL PRIMARY KEY,

    transaction_id BIGINT NOT NULL
        REFERENCES transaction(id),

    status VARCHAR(50) NOT NULL,

    event_datetime TIMESTAMP NOT NULL DEFAULT NOW()
);