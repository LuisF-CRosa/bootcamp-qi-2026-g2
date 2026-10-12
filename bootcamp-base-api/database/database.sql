-- A primeira versao comporta apenas uma republica.
CREATE UNIQUE INDEX one_institutional_client
    ON client (client_type)
    WHERE client_type = 'INSTITUTIONAL_CLIENT';

CREATE TABLE account_status (
    id                          SMALLSERIAL PRIMARY KEY,
    enumerator                  VARCHAR(30) NOT NULL UNIQUE
);

INSERT INTO account_status (enumerator) VALUES ('ACTIVE'), ('CLOSED');

CREATE TABLE account (
    id                          BIGSERIAL PRIMARY KEY,
    account_key                 CHAR(36) NOT NULL UNIQUE,
    client_id                   BIGINT NOT NULL REFERENCES client(id),
    account_type                VARCHAR(20) NOT NULL,
    status_id                   SMALLINT NOT NULL REFERENCES account_status(id),
    balance_cents               BIGINT NOT NULL DEFAULT 0,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT account_type_valid CHECK (
        account_type IN ('PERSONAL', 'HOUSE', 'EMERGENCY')
    ),
    CONSTRAINT account_balance_nonnegative CHECK (balance_cents >= 0)
);

-- No maximo uma conta ativa de cada tipo por cliente. O estado ACTIVE
-- foi inserido primeiro, logo tem id 1 nesta inicializacao limpa.
CREATE UNIQUE INDEX one_active_account_per_type
    ON account (client_id, account_type) WHERE status_id = 1;
CREATE INDEX account_by_client ON account (client_id, id);

CREATE TABLE account_status_event (
    id                          BIGSERIAL PRIMARY KEY,
    account_id                  BIGINT NOT NULL REFERENCES account(id),
    status_id                   SMALLINT NOT NULL REFERENCES account_status(id),
    event_datetime              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason                      VARCHAR(255)
);
CREATE INDEX account_status_event_history
    ON account_status_event (account_id, event_datetime, id);

CREATE TABLE transaction_status (
    id                          SMALLSERIAL PRIMARY KEY,
    enumerator                  VARCHAR(30) NOT NULL UNIQUE
);

INSERT INTO transaction_status (enumerator) VALUES
    ('CREATED'), ('SUCCESS'), ('FAILED');

-- "transaction" e palavra especial em alguns contextos SQL; o nome
-- financial_transaction evita aspas nas consultas.
CREATE TABLE financial_transaction (
    id                          BIGSERIAL PRIMARY KEY,
    transaction_key             CHAR(36) NOT NULL UNIQUE,
    operation_type              VARCHAR(30) NOT NULL,
    source_account_id           BIGINT REFERENCES account(id),
    destination_account_id      BIGINT NOT NULL REFERENCES account(id),
    gross_amount_cents          BIGINT NOT NULL,
    fee_amount_cents            BIGINT NOT NULL DEFAULT 0,
    idempotency_key             VARCHAR(255) NOT NULL UNIQUE,
    request_fingerprint         CHAR(64) NOT NULL,
    status_id                   SMALLINT NOT NULL REFERENCES transaction_status(id),
    response_status             SMALLINT,
    response_body               JSONB,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT transaction_type_valid CHECK (
        operation_type IN ('SIMULATED_DEPOSIT', 'TRANSFER')
    ),
    CONSTRAINT transaction_amount_positive CHECK (gross_amount_cents > 0),
    CONSTRAINT transaction_fee_valid CHECK (
        fee_amount_cents >= 0 AND fee_amount_cents <= gross_amount_cents
    ),
    CONSTRAINT transaction_accounts_valid CHECK (
        (operation_type = 'SIMULATED_DEPOSIT'
            AND source_account_id IS NULL AND fee_amount_cents = 0)
        OR
        (operation_type = 'TRANSFER'
            AND source_account_id IS NOT NULL
            AND source_account_id <> destination_account_id)
    ),
    CONSTRAINT transaction_response_together CHECK (
        (response_status IS NULL AND response_body IS NULL)
        OR (response_status IS NOT NULL AND response_body IS NOT NULL)
    )
);

CREATE TABLE transaction_status_event (
    id                          BIGSERIAL PRIMARY KEY,
    transaction_id              BIGINT NOT NULL REFERENCES financial_transaction(id),
    status_id                   SMALLINT NOT NULL REFERENCES transaction_status(id),
    event_datetime              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX transaction_status_event_history
    ON transaction_status_event (transaction_id, event_datetime, id);

CREATE TABLE account_entry (
    id                          BIGSERIAL PRIMARY KEY,
    transaction_id              BIGINT NOT NULL REFERENCES financial_transaction(id),
    account_id                  BIGINT NOT NULL REFERENCES account(id),
    signed_amount_cents         BIGINT NOT NULL,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT account_entry_nonzero CHECK (signed_amount_cents <> 0)
);
CREATE INDEX account_entry_statement
    ON account_entry (account_id, created_at DESC, id DESC);

-- Regras entre tabelas (PERSONAL pertence a pessoa fisica; HOUSE e
-- EMERGENCY pertencem a instituicao), a soma dos lancamentos e a ordem
-- dos locks ficam no controller/repository da proxima etapa. Este schema
-- protege tipos, unicidade, chaves estrangeiras e saldo nao negativo.
