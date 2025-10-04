# FinSight Database Documentation

This directory contains the database schema and setup tools for the FinSight Expense Management System.

## 🗄️ Database Structure

FinSight uses SQLite as its database engine with the following tables:

### Core Tables

1. **companies** - Company/organization information
2. **users** - User accounts and authentication
3. **expense_claims** - Expense claim records
4. **approvals** - Approval workflow records
5. **approval_rules** - Company-specific approval policies
6. **approval_sequences** - Approval hierarchy definitions
7. **audit_log** - System activity audit trail

### Views

- **user_summary** - Users with company and manager information
- **expense_summary** - Expenses with approval status
- **pending_approvals** - Active approvals waiting for review

## 🚀 Quick Setup

### Option 1: Automatic Setup (Recommended)

```bash
# Create database with schema only
python setup_database.py

# Create database with sample data for testing
python setup_database.py --sample-data
```

### Option 2: Manual Setup

```bash
# Create database directory
mkdir -p database

# Create database from schema
sqlite3 database/expense_management.db < database_schema.sql
```

### Option 3: Using the Application

```bash
# Run the application - it will create the database automatically
python run.py
```

## 📊 Sample Data

When using `--sample-data` flag, the following demo accounts are created:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@democompany.com | admin123 |
| Manager | manager@democompany.com | manager123 |
| Employee | employee@democompany.com | employee123 |

⚠️ **Security Warning**: Change these passwords immediately in production!

## 🔧 Database Configuration

The database is configured with:

- **WAL Mode**: Better concurrency support
- **Foreign Keys**: Enabled for data integrity
- **Indexes**: Optimized for common queries
- **Triggers**: Automatic timestamp updates
- **Views**: Pre-built queries for reporting

## 📋 Schema Details

### Companies Table
```sql
CREATE TABLE companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    country_code TEXT NOT NULL DEFAULT 'US',
    base_currency TEXT NOT NULL DEFAULT 'USD',
    -- ... additional fields
);
```

### Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role_type TEXT NOT NULL CHECK (role_type IN ('admin', 'manager', 'employee')),
    -- ... additional fields
);
```

### Expense Claims Table
```sql
CREATE TABLE expense_claims (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    -- ... additional fields
);
```

## 🔍 Useful Queries

### Get all pending expenses for a company
```sql
SELECT * FROM expense_summary 
WHERE company_name = 'Your Company' AND status = 'pending';
```

### Get pending approvals for a manager
```sql
SELECT * FROM pending_approvals 
WHERE approver_name = 'Manager Name';
```

### Get user activity
```sql
SELECT * FROM audit_log 
WHERE user_id = 1 
ORDER BY created_at DESC LIMIT 10;
```

## 🛠️ Maintenance

### Backup Database
```bash
# Create backup
cp database/expense_management.db database/backup_$(date +%Y%m%d).db

# Or use SQLite backup command
sqlite3 database/expense_management.db ".backup database/backup_$(date +%Y%m%d).db"
```

### Database Statistics
```bash
# Check database size and table info
sqlite3 database/expense_management.db ".dbinfo"

# Analyze database performance
sqlite3 database/expense_management.db "ANALYZE;"
```

### Reset Database
```bash
# Remove existing database
rm database/expense_management.db

# Recreate from schema
python setup_database.py --sample-data
```

## 🔒 Security Considerations

1. **Password Hashing**: All passwords are hashed using PBKDF2-SHA256
2. **Foreign Keys**: Enabled to maintain referential integrity
3. **Input Validation**: Schema enforces data types and constraints
4. **Audit Trail**: All actions are logged in audit_log table
5. **Access Control**: Role-based permissions (admin/manager/employee)

## 📱 Database Tools

### Available Scripts

- `setup_database.py` - Create database from schema
- `check_database.py` - Inspect database contents
- `database_schema.sql` - Complete schema definition

### External Tools

You can also use standard SQLite tools:

```bash
# Command line interface
sqlite3 database/expense_management.db

# GUI tools
# - DB Browser for SQLite
# - SQLiteStudio
# - DBeaver
```

## 🚨 Troubleshooting

### Database Locked Error
```bash
# Check for active connections
lsof database/expense_management.db

# Or restart the application
pkill python
python run.py
```

### Schema Updates
```bash
# Backup first
cp database/expense_management.db database/backup.db

# Apply schema changes manually or recreate database
python setup_database.py
```

### Corrupted Database
```bash
# Check integrity
sqlite3 database/expense_management.db "PRAGMA integrity_check;"

# Repair if needed
sqlite3 database/expense_management.db ".recover" | sqlite3 database/recovered.db
```

## 📈 Performance Tips

1. **Regular ANALYZE**: Run `ANALYZE;` periodically for query optimization
2. **WAL Mode**: Already enabled for better concurrency
3. **Proper Indexes**: All common queries are indexed
4. **Connection Pooling**: Application uses connection pooling
5. **Batch Operations**: Use transactions for multiple operations

## 🔄 Migration Support

The schema includes version tracking:

```sql
SELECT * FROM schema_version;
```

For future updates, migration scripts can check the current version and apply necessary changes.

---

For more information, see the main [README.md](../README.md) or contact the development team.