BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS auth_version INTEGER,
    ADD COLUMN IF NOT EXISTS consumption_multiplier NUMERIC(3, 2),
    ADD COLUMN IF NOT EXISTS distribution_level INTEGER,
    ADD COLUMN IF NOT EXISTS distribution_parent_id INTEGER,
    ADD COLUMN IF NOT EXISTS commission_rate NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS invite_code VARCHAR(32),
    ADD COLUMN IF NOT EXISTS distribution_enabled BOOLEAN,
    ADD COLUMN IF NOT EXISTS commission_available_cents INTEGER,
    ADD COLUMN IF NOT EXISTS commission_frozen_cents INTEGER,
    ADD COLUMN IF NOT EXISTS commission_withdrawn_cents INTEGER;

UPDATE users
SET auth_version = COALESCE(auth_version, 0),
    consumption_multiplier = COALESCE(consumption_multiplier, 1.00),
    distribution_enabled = COALESCE(distribution_enabled, FALSE),
    commission_available_cents = COALESCE(commission_available_cents, 0),
    commission_frozen_cents = COALESCE(commission_frozen_cents, 0),
    commission_withdrawn_cents = COALESCE(commission_withdrawn_cents, 0);

ALTER TABLE users
    ALTER COLUMN auth_version SET NOT NULL,
    ALTER COLUMN consumption_multiplier SET NOT NULL,
    ALTER COLUMN distribution_enabled SET NOT NULL,
    ALTER COLUMN commission_available_cents SET NOT NULL,
    ALTER COLUMN commission_frozen_cents SET NOT NULL,
    ALTER COLUMN commission_withdrawn_cents SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'users_distribution_parent_id_fkey') THEN
        ALTER TABLE users
            ADD CONSTRAINT users_distribution_parent_id_fkey
            FOREIGN KEY (distribution_parent_id) REFERENCES users (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_users_consumption_multiplier') THEN
        ALTER TABLE users
            ADD CONSTRAINT ck_users_consumption_multiplier
            CHECK (consumption_multiplier >= 0.01 AND consumption_multiplier <= 9.99);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_users_distribution_level') THEN
        ALTER TABLE users
            ADD CONSTRAINT ck_users_distribution_level
            CHECK (distribution_level IS NULL OR distribution_level IN (1, 2, 3));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_users_commission_rate') THEN
        ALTER TABLE users
            ADD CONSTRAINT ck_users_commission_rate
            CHECK (commission_rate IS NULL OR (commission_rate >= 0 AND commission_rate <= 100));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_users_commission_balances') THEN
        ALTER TABLE users
            ADD CONSTRAINT ck_users_commission_balances
            CHECK (
                commission_available_cents >= 0
                AND commission_frozen_cents >= 0
                AND commission_withdrawn_cents >= 0
            );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_users_distribution_parent
    ON users (distribution_parent_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_invite_code
    ON users (invite_code);

ALTER TABLE credit_orders
    ADD COLUMN IF NOT EXISTS distribution_snapshot_json TEXT,
    ADD COLUMN IF NOT EXISTS distribution_root_user_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'credit_orders_distribution_root_user_id_fkey') THEN
        ALTER TABLE credit_orders
            ADD CONSTRAINT credit_orders_distribution_root_user_id_fkey
            FOREIGN KEY (distribution_root_user_id) REFERENCES users (id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_credit_orders_distribution_root_status
    ON credit_orders (distribution_root_user_id, status);

CREATE TABLE IF NOT EXISTS commission_withdrawals (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id),
    amount_cents INTEGER NOT NULL,
    alipay_name VARCHAR(100) NOT NULL,
    alipay_account VARCHAR(150) NOT NULL,
    status VARCHAR(24) NOT NULL,
    reject_reason VARCHAR(255),
    payment_reference VARCHAR(100),
    voucher_url VARCHAR(500),
    voucher_object_key VARCHAR(500),
    reviewed_by INTEGER REFERENCES users (id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT ck_commission_withdrawals_amount CHECK (amount_cents >= 10000),
    CONSTRAINT ck_commission_withdrawals_status
        CHECK (status IN ('pending_review', 'pending_payment', 'paid', 'rejected'))
);

CREATE INDEX IF NOT EXISTS ix_commission_withdrawals_user_created
    ON commission_withdrawals (user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_commission_withdrawals_status_created
    ON commission_withdrawals (status, created_at);

CREATE TABLE IF NOT EXISTS commission_transactions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id),
    source_user_id INTEGER REFERENCES users (id),
    order_id VARCHAR(36) REFERENCES credit_orders (id),
    withdrawal_id VARCHAR(36) REFERENCES commission_withdrawals (id),
    type VARCHAR(24) NOT NULL,
    available_delta_cents INTEGER NOT NULL,
    frozen_delta_cents INTEGER NOT NULL,
    available_after_cents INTEGER NOT NULL,
    frozen_after_cents INTEGER NOT NULL,
    source_amount_cents INTEGER,
    commission_rate NUMERIC(5, 2),
    note VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_commission_transactions_user_created
    ON commission_transactions (user_id, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_commission_transactions_order_user_type
    ON commission_transactions (order_id, user_id, type);

CREATE TABLE IF NOT EXISTS coupon_codes (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(32) NOT NULL,
    credits INTEGER NOT NULL,
    usage_limit INTEGER,
    used_count INTEGER NOT NULL,
    enabled BOOLEAN NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by_user_id INTEGER NOT NULL REFERENCES users (id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT ck_coupon_codes_credits CHECK (credits >= 1 AND credits <= 10000000),
    CONSTRAINT ck_coupon_codes_usage_limit
        CHECK (usage_limit IS NULL OR (usage_limit > 0 AND usage_limit <= 1000000)),
    CONSTRAINT ck_coupon_codes_used_count CHECK (used_count >= 0),
    CONSTRAINT ck_coupon_codes_usage_count CHECK (usage_limit IS NULL OR used_count <= usage_limit)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_coupon_codes_code
    ON coupon_codes (code);
CREATE INDEX IF NOT EXISTS ix_coupon_codes_status
    ON coupon_codes (deleted_at, enabled);

CREATE TABLE IF NOT EXISTS coupon_redemptions (
    id VARCHAR(36) PRIMARY KEY,
    coupon_code_id VARCHAR(36) NOT NULL REFERENCES coupon_codes (id),
    user_id INTEGER NOT NULL REFERENCES users (id),
    code_snapshot VARCHAR(32) NOT NULL,
    credits_snapshot INTEGER NOT NULL,
    credit_transaction_id VARCHAR(36) NOT NULL UNIQUE REFERENCES credit_transactions (id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT uq_coupon_redemptions_coupon_user UNIQUE (coupon_code_id, user_id)
);

CREATE INDEX IF NOT EXISTS ix_coupon_redemptions_user_created
    ON coupon_redemptions (user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_coupon_redemptions_coupon_created
    ON coupon_redemptions (coupon_code_id, created_at);

COMMIT;
