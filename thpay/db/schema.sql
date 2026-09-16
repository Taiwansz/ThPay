-- ThPay Core Relational Schema
-- Version: 2026.09.01_foundation
-- Strict foreign keys, indexes, UTC timestamps, audit-ready

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(64) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- 1. Multi-tenant & Organization Hierarchy
CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    cnpj VARCHAR(18) NOT NULL UNIQUE,
    corporate_name VARCHAR(255) NOT NULL,
    trade_name VARCHAR(255),
    tax_regime VARCHAR(64) NOT NULL DEFAULT 'LUCRO_REAL',
    cnae VARCHAR(16) NOT NULL DEFAULT '6201-5/01',
    fpas VARCHAR(8) NOT NULL DEFAULT '507',
    other_entities_code VARCHAR(8) DEFAULT '0079',
    rat_basic DECIMAL(5, 4) NOT NULL DEFAULT 0.0200,
    fap DECIMAL(5, 4) NOT NULL DEFAULT 1.0000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS branches (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(32) NOT NULL,
    name VARCHAR(255) NOT NULL,
    cnpj VARCHAR(18) NOT NULL,
    address_street VARCHAR(255),
    address_number VARCHAR(32),
    address_city VARCHAR(128),
    address_state VARCHAR(2),
    address_zip VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, code)
);

CREATE TABLE IF NOT EXISTS departments (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(32) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, code)
);

CREATE TABLE IF NOT EXISTS cost_centers (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(32) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, code)
);

CREATE TABLE IF NOT EXISTS positions (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    cbo VARCHAR(16) NOT NULL,
    standard_salary DECIMAL(12, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, code)
);

-- 2. Authentication, Users & RBAC
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id VARCHAR(36) REFERENCES companies(id) ON DELETE SET NULL,
    employee_id VARCHAR(36),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(64) NOT NULL DEFAULT 'COLABORADOR_SELF_SERVICE',
    is_active INTEGER NOT NULL DEFAULT 1,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roles (
    code VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_code VARCHAR(64) NOT NULL REFERENCES roles(code) ON DELETE CASCADE,
    permission_code VARCHAR(64) NOT NULL,
    PRIMARY KEY (role_code, permission_code)
);

CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Core Employees & Contracts
CREATE TABLE IF NOT EXISTS employees (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    cpf VARCHAR(14) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    social_name VARCHAR(255),
    birth_date DATE NOT NULL,
    gender VARCHAR(1) DEFAULT 'M',
    marital_status VARCHAR(32) DEFAULT 'SOLTEIRO',
    nationality VARCHAR(64) DEFAULT 'BRASILEIRA',
    birth_city VARCHAR(128),
    birth_state VARCHAR(2),
    education_level VARCHAR(64) DEFAULT 'SUPERIOR_COMPLETO',
    mother_name VARCHAR(255),
    father_name VARCHAR(255),
    personal_email VARCHAR(255),
    corporate_email VARCHAR(255),
    phone_mobile VARCHAR(32),
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, cpf)
);

CREATE TABLE IF NOT EXISTS employee_addresses (
    id VARCHAR(36) PRIMARY KEY,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    zip_code VARCHAR(10) NOT NULL,
    street VARCHAR(255) NOT NULL,
    number VARCHAR(32) NOT NULL,
    complement VARCHAR(128),
    neighborhood VARCHAR(128) NOT NULL,
    city VARCHAR(128) NOT NULL,
    state VARCHAR(2) NOT NULL,
    country VARCHAR(64) DEFAULT 'Brasil',
    is_primary INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employee_documents (
    id VARCHAR(36) PRIMARY KEY,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    document_type VARCHAR(32) NOT NULL,
    document_number VARCHAR(64) NOT NULL,
    issuer VARCHAR(32),
    issuer_state VARCHAR(2),
    issue_date DATE,
    expiration_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employee_bank_accounts (
    id VARCHAR(36) PRIMARY KEY,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    bank_code VARCHAR(10) NOT NULL,
    bank_name VARCHAR(128) NOT NULL,
    agency VARCHAR(16) NOT NULL,
    account_number VARCHAR(32) NOT NULL,
    account_type VARCHAR(32) DEFAULT 'CORRENTE',
    pix_key VARCHAR(128),
    is_primary INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employee_dependents (
    id VARCHAR(36) PRIMARY KEY,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    cpf VARCHAR(14),
    birth_date DATE,
    relationship VARCHAR(32) NOT NULL,
    is_irrf_dependent INTEGER NOT NULL DEFAULT 1,
    is_family_salary_dependent INTEGER NOT NULL DEFAULT 0,
    is_health_plan_dependent INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employment_contracts (
    id VARCHAR(36) PRIMARY KEY,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    branch_id VARCHAR(36) REFERENCES branches(id),
    department_id VARCHAR(36) REFERENCES departments(id),
    cost_center_id VARCHAR(36) REFERENCES cost_centers(id),
    position_id VARCHAR(36) REFERENCES positions(id),
    registration_number VARCHAR(32) NOT NULL,
    hire_date DATE NOT NULL,
    category VARCHAR(8) NOT NULL DEFAULT '101',
    contract_type VARCHAR(32) NOT NULL DEFAULT 'INDETERMINATE',
    probation_days_1 INTEGER DEFAULT 45,
    probation_days_2 INTEGER DEFAULT 45,
    base_salary DECIMAL(12, 2) NOT NULL,
    monthly_hours INTEGER NOT NULL DEFAULT 220,
    work_schedule VARCHAR(64) DEFAULT '44h semanais (Seg-Sex 8h48)',
    work_modality VARCHAR(32) DEFAULT 'PRESENTIAL',
    is_active INTEGER NOT NULL DEFAULT 1,
    valid_from DATE NOT NULL,
    valid_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, registration_number)
);

CREATE TABLE IF NOT EXISTS employee_benefits (
    id VARCHAR(36) PRIMARY KEY,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    benefit_type VARCHAR(32) NOT NULL,
    va_percentage INTEGER DEFAULT 50,
    vr_percentage INTEGER DEFAULT 50,
    total_amount DECIMAL(10, 2) DEFAULT 0.00,
    opt_out INTEGER DEFAULT 0,
    details_json TEXT,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Admission Batches, Import Engine & Onboarding
CREATE TABLE IF NOT EXISTS admission_batches (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    batch_code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    target_start_date DATE NOT NULL,
    branch_id VARCHAR(36) REFERENCES branches(id),
    expected_count INTEGER NOT NULL DEFAULT 1,
    responsible_user_id VARCHAR(36) REFERENCES users(id),
    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admission_import_files (
    id VARCHAR(36) PRIMARY KEY,
    batch_id VARCHAR(36) NOT NULL REFERENCES admission_batches(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(128) NOT NULL,
    file_hash_sha256 VARCHAR(64) NOT NULL,
    storage_path VARCHAR(512) NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    uploaded_by_user_id VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admission_column_mappings (
    id VARCHAR(36) PRIMARY KEY,
    batch_id VARCHAR(36) NOT NULL REFERENCES admission_batches(id) ON DELETE CASCADE,
    source_column VARCHAR(128) NOT NULL,
    target_field VARCHAR(128) NOT NULL,
    default_value TEXT,
    is_ignored INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(batch_id, source_column)
);

CREATE TABLE IF NOT EXISTS admission_templates (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    template_data_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admission_rows (
    id VARCHAR(36) PRIMARY KEY,
    batch_id VARCHAR(36) NOT NULL REFERENCES admission_batches(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    raw_data_json TEXT NOT NULL,
    parsed_data_json TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'IMPORTED',
    error_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    fingerprint VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(batch_id, row_number)
);

CREATE TABLE IF NOT EXISTS admission_validation_issues (
    id VARCHAR(36) PRIMARY KEY,
    row_id VARCHAR(36) NOT NULL REFERENCES admission_rows(id) ON DELETE CASCADE,
    batch_id VARCHAR(36) NOT NULL REFERENCES admission_batches(id) ON DELETE CASCADE,
    severity VARCHAR(16) NOT NULL, -- ERROR or WARNING
    field_name VARCHAR(128) NOT NULL,
    error_code VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    suggested_action TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admissions (
    id VARCHAR(36) PRIMARY KEY,
    batch_id VARCHAR(36) NOT NULL REFERENCES admission_batches(id) ON DELETE CASCADE,
    row_id VARCHAR(36) REFERENCES admission_rows(id) ON DELETE SET NULL,
    employee_id VARCHAR(36) REFERENCES employees(id) ON DELETE SET NULL,
    candidate_name VARCHAR(255) NOT NULL,
    candidate_cpf VARCHAR(14) NOT NULL,
    candidate_email VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'IMPORTADO',
    pre_admission_token VARCHAR(64) UNIQUE,
    pre_admission_token_expires_at TIMESTAMP,
    pre_admission_completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admission_tasks (
    id VARCHAR(36) PRIMARY KEY,
    admission_id VARCHAR(36) NOT NULL REFERENCES admissions(id) ON DELETE CASCADE,
    employee_id VARCHAR(36) REFERENCES employees(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(64) DEFAULT 'ONBOARDING',
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    due_date DATE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Decoupled eSocial Events
CREATE TABLE IF NOT EXISTS esocial_events (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    admission_id VARCHAR(36) REFERENCES admissions(id) ON DELETE SET NULL,
    employee_id VARCHAR(36) REFERENCES employees(id) ON DELETE SET NULL,
    event_type VARCHAR(16) NOT NULL, -- S-2190 or S-2200
    event_version VARCHAR(16) NOT NULL DEFAULT 'v1_3',
    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT', -- DRAFT, QUEUED, TRANSMITTED, ACCEPTED, REJECTED
    payload_xml TEXT,
    payload_json TEXT NOT NULL,
    protocol_number VARCHAR(64),
    receipt_number VARCHAR(64),
    rejection_code VARCHAR(32),
    rejection_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    sent_at TIMESTAMP,
    receipt_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Audit Trail (Append-Only)
CREATE TABLE IF NOT EXISTS audit_trail (
    id VARCHAR(36) PRIMARY KEY,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actor_user_id VARCHAR(36),
    actor_email VARCHAR(255),
    actor_role VARCHAR(64),
    ip_address VARCHAR(45),
    tenant_id VARCHAR(36),
    company_id VARCHAR(36),
    action VARCHAR(128) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    before_json TEXT,
    after_json TEXT,
    reason TEXT,
    correlation_id VARCHAR(64)
);

-- 7. Document Storage Registry
CREATE TABLE IF NOT EXISTS stored_documents (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    document_type VARCHAR(64) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    storage_path VARCHAR(512) NOT NULL,
    mime_type VARCHAR(128) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL,
    uploaded_by_user_id VARCHAR(36),
    is_validated INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Payroll Runs & Calculated Payslips
CREATE TABLE IF NOT EXISTS payroll_runs (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    competence VARCHAR(7) NOT NULL, -- YYYY-MM
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    total_gross DECIMAL(14, 2) DEFAULT 0.00,
    total_net DECIMAL(14, 2) DEFAULT 0.00,
    total_inss_patronal DECIMAL(14, 2) DEFAULT 0.00,
    total_fgts DECIMAL(14, 2) DEFAULT 0.00,
    calculated_at TIMESTAMP,
    closed_at TIMESTAMP,
    hash_lock VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, competence)
);

CREATE TABLE IF NOT EXISTS payslips (
    id VARCHAR(36) PRIMARY KEY,
    payroll_run_id VARCHAR(36) NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    contract_id VARCHAR(36) NOT NULL REFERENCES employment_contracts(id) ON DELETE CASCADE,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    competence VARCHAR(7) NOT NULL,
    gross_total DECIMAL(12, 2) NOT NULL,
    discounts_total DECIMAL(12, 2) NOT NULL,
    net_total DECIMAL(12, 2) NOT NULL,
    inss_base DECIMAL(12, 2) NOT NULL,
    irrf_base DECIMAL(12, 2) NOT NULL,
    fgts_base DECIMAL(12, 2) NOT NULL,
    fgts_amount DECIMAL(12, 2) NOT NULL,
    hash_lock VARCHAR(64),
    items_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for high performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_employees_cpf ON employees(cpf);
CREATE INDEX IF NOT EXISTS idx_contracts_employee ON employment_contracts(employee_id);
CREATE INDEX IF NOT EXISTS idx_admission_batches_company ON admission_batches(company_id);
CREATE INDEX IF NOT EXISTS idx_admission_rows_batch ON admission_rows(batch_id);
CREATE INDEX IF NOT EXISTS idx_admission_issues_row ON admission_validation_issues(row_id);
CREATE INDEX IF NOT EXISTS idx_esocial_admission ON esocial_events(admission_id);
CREATE INDEX IF NOT EXISTS idx_audit_occurred_at ON audit_trail(occurred_at);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_trail(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_stored_docs_entity ON stored_documents(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_payslips_competence ON payslips(competence);
