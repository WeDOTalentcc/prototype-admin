CREATE TABLE IF NOT EXISTS credit_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(100) NOT NULL UNIQUE,
    plan_type VARCHAR(50) NOT NULL DEFAULT 'free',
    balance INTEGER NOT NULL DEFAULT 0,
    lifetime_purchased INTEGER NOT NULL DEFAULT 0,
    lifetime_consumed INTEGER NOT NULL DEFAULT 0,
    lifetime_bonus INTEGER NOT NULL DEFAULT 0,
    low_balance_threshold INTEGER NOT NULL DEFAULT 20,
    reset_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_credit_accounts_company ON credit_accounts (company_id);

CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(30) NOT NULL,
    action_type VARCHAR(50),
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    description VARCHAR(500),
    reference_type VARCHAR(50),
    reference_id VARCHAR(100),
    performed_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_credit_tx_company_created ON credit_transactions (company_id, created_at);
CREATE INDEX IF NOT EXISTS ix_credit_transactions_company_id ON credit_transactions (company_id);
CREATE INDEX IF NOT EXISTS ix_credit_transactions_transaction_type ON credit_transactions (transaction_type);
CREATE INDEX IF NOT EXISTS ix_credit_tx_action_type ON credit_transactions (action_type);

ALTER TABLE credit_accounts ADD COLUMN IF NOT EXISTS plan_type VARCHAR(50) NOT NULL DEFAULT 'free';
ALTER TABLE credit_accounts ADD COLUMN IF NOT EXISTS low_balance_threshold INTEGER NOT NULL DEFAULT 20;
ALTER TABLE credit_accounts ADD COLUMN IF NOT EXISTS reset_date TIMESTAMP;
ALTER TABLE credit_transactions ADD COLUMN IF NOT EXISTS action_type VARCHAR(50);
