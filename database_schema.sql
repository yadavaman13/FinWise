-- FinSight Database Schema
-- Complete database structure for FinSight Expense Management System
-- This file can be used to recreate the database structure without sensitive data

-- Create database (SQLite will create it automatically when first table is created)
-- Usage: sqlite3 database/expense_management.db < database_schema.sql

-- ===== COMPANIES TABLE =====
-- Stores company information and settings
CREATE TABLE IF NOT EXISTS companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    country_code TEXT NOT NULL DEFAULT 'US',
    base_currency TEXT NOT NULL DEFAULT 'USD',
    address TEXT,
    phone TEXT,
    email TEXT,
    tax_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== USERS TABLE =====
-- Stores user accounts and authentication information
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role_type TEXT NOT NULL CHECK (role_type IN ('admin', 'manager', 'employee')),
    manager_id INTEGER,
    department TEXT,
    employee_id TEXT,
    phone TEXT,
    is_active BOOLEAN DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (manager_id) REFERENCES users(user_id)
);

-- ===== EXPENSE CLAIMS TABLE =====
-- Stores expense claim records
CREATE TABLE IF NOT EXISTS expense_claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    amount DECIMAL(10,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    converted_amount DECIMAL(10,2) NOT NULL,
    expense_date DATE NOT NULL,
    receipt_url TEXT,
    receipt_data TEXT, -- JSON data from OCR processing
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- ===== APPROVALS TABLE =====
-- Stores approval workflow records
CREATE TABLE IF NOT EXISTS approvals (
    approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    approver_id INTEGER NOT NULL,
    sequence_order INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    comments TEXT,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES expense_claims(claim_id),
    FOREIGN KEY (approver_id) REFERENCES users(user_id)
);

-- ===== APPROVAL RULES TABLE =====
-- Stores company-specific approval rules and policies
CREATE TABLE IF NOT EXISTS approval_rules (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    category TEXT,
    min_amount DECIMAL(10,2),
    max_amount DECIMAL(10,2),
    requires_receipt BOOLEAN DEFAULT 0,
    approval_levels INTEGER DEFAULT 1,
    auto_approve_threshold DECIMAL(10,2),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- ===== APPROVAL SEQUENCES TABLE =====
-- Defines the approval sequence/hierarchy for companies
CREATE TABLE IF NOT EXISTS approval_sequences (
    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    sequence_order INTEGER NOT NULL,
    is_manager_approver BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ===== AUDIT LOG TABLE =====
-- Stores audit trail for all system activities
CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id INTEGER,
    details TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ===== INDEXES FOR PERFORMANCE =====
-- Create indexes for frequently queried columns

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_company ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_users_manager ON users(manager_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_type);

-- Expense claims indexes
CREATE INDEX IF NOT EXISTS idx_expense_claims_user ON expense_claims(user_id);
CREATE INDEX IF NOT EXISTS idx_expense_claims_company ON expense_claims(company_id);
CREATE INDEX IF NOT EXISTS idx_expense_claims_status ON expense_claims(status);
CREATE INDEX IF NOT EXISTS idx_expense_claims_date ON expense_claims(expense_date);
CREATE INDEX IF NOT EXISTS idx_expense_claims_created ON expense_claims(created_at);

-- Approvals indexes
CREATE INDEX IF NOT EXISTS idx_approvals_claim ON approvals(claim_id);
CREATE INDEX IF NOT EXISTS idx_approvals_approver ON approvals(approver_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);

-- Approval sequences indexes
CREATE INDEX IF NOT EXISTS idx_approval_sequences_company ON approval_sequences(company_id);
CREATE INDEX IF NOT EXISTS idx_approval_sequences_user ON approval_sequences(user_id);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);

-- ===== SAMPLE DATA STRUCTURE (For Testing) =====
-- Uncomment below to insert sample data for development/testing


-- ===== TRIGGERS FOR AUTOMATIC UPDATES =====
-- Update timestamp triggers

-- Update companies.updated_at on UPDATE
CREATE TRIGGER IF NOT EXISTS update_companies_timestamp 
    AFTER UPDATE ON companies
    FOR EACH ROW
    BEGIN
        UPDATE companies SET updated_at = CURRENT_TIMESTAMP WHERE company_id = NEW.company_id;
    END;

-- Update users.updated_at on UPDATE
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
    AFTER UPDATE ON users
    FOR EACH ROW
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
    END;

-- Update expense_claims.updated_at on UPDATE
CREATE TRIGGER IF NOT EXISTS update_expense_claims_timestamp 
    AFTER UPDATE ON expense_claims
    FOR EACH ROW
    BEGIN
        UPDATE expense_claims SET updated_at = CURRENT_TIMESTAMP WHERE claim_id = NEW.claim_id;
    END;

-- ===== VIEWS FOR COMMON QUERIES =====
-- Create useful views for reporting and dashboards

-- User summary view with company information
CREATE VIEW IF NOT EXISTS user_summary AS
SELECT 
    u.user_id,
    u.name,
    u.email,
    u.role_type,
    u.department,
    u.is_active,
    c.name as company_name,
    c.base_currency,
    m.name as manager_name
FROM users u
LEFT JOIN companies c ON u.company_id = c.company_id
LEFT JOIN users m ON u.manager_id = m.user_id;

-- Expense summary view with approval status
CREATE VIEW IF NOT EXISTS expense_summary AS
SELECT 
    ec.claim_id,
    ec.title,
    ec.category,
    ec.amount,
    ec.currency,
    ec.converted_amount,
    ec.status,
    ec.expense_date,
    ec.created_at,
    u.name as employee_name,
    c.name as company_name,
    c.base_currency,
    COUNT(a.approval_id) as total_approvals,
    SUM(CASE WHEN a.status = 'approved' THEN 1 ELSE 0 END) as approved_count,
    SUM(CASE WHEN a.status = 'rejected' THEN 1 ELSE 0 END) as rejected_count
FROM expense_claims ec
LEFT JOIN users u ON ec.user_id = u.user_id
LEFT JOIN companies c ON ec.company_id = c.company_id
LEFT JOIN approvals a ON ec.claim_id = a.claim_id
GROUP BY ec.claim_id;

-- Pending approvals view for managers/admins
CREATE VIEW IF NOT EXISTS pending_approvals AS
SELECT 
    a.approval_id,
    a.claim_id,
    ec.title,
    ec.amount,
    ec.currency,
    ec.converted_amount,
    ec.expense_date,
    u.name as employee_name,
    approver.name as approver_name,
    c.name as company_name,
    a.sequence_order
FROM approvals a
JOIN expense_claims ec ON a.claim_id = ec.claim_id
JOIN users u ON ec.user_id = u.user_id
JOIN users approver ON a.approver_id = approver.user_id
JOIN companies c ON ec.company_id = c.company_id
WHERE a.status = 'pending' AND ec.status = 'pending'
ORDER BY ec.created_at ASC;

-- ===== PRAGMA SETTINGS FOR OPTIMIZATION =====
-- Configure SQLite for better performance and reliability

PRAGMA foreign_keys = ON;          -- Enable foreign key constraints
PRAGMA journal_mode = WAL;         -- Use WAL mode for better concurrency
PRAGMA synchronous = NORMAL;       -- Balance between safety and speed
PRAGMA cache_size = 2000;          -- Increase cache size
PRAGMA temp_store = memory;        -- Store temporary tables in memory
PRAGMA busy_timeout = 60000;       -- 60 second timeout for locked database

-- ===== SCHEMA VERSION TRACKING =====
-- Track schema version for migrations

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert current schema version
INSERT OR REPLACE INTO schema_version (version, description) VALUES 
(1, 'Initial FinSight database schema with all core tables, indexes, triggers, and views');

-- ===== END OF SCHEMA =====
-- Schema created successfully for FinSight Expense Management System
-- Date: 2025-10-04
-- Version: 1.0