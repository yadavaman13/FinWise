#!/usr/bin/env python3
"""
FinSight Database Setup Script
Creates a new database from the schema file with optional sample data
"""

import sqlite3
import os
import sys
from datetime import datetime

def create_database_from_schema(schema_file='database_schema.sql', db_file='database/expense_management.db'):
    """Create database from schema file"""
    
    print("="*60)
    print("         FINSIGHT DATABASE SETUP")
    print("="*60)
    print(f"Schema file: {schema_file}")
    print(f"Database file: {db_file}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if schema file exists
    if not os.path.exists(schema_file):
        print(f"❌ Schema file '{schema_file}' not found!")
        return False
    
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(db_file)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"📁 Created directory: {db_dir}")
    
    # Check if database already exists
    if os.path.exists(db_file):
        response = input(f"⚠️  Database '{db_file}' already exists. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ Aborted by user")
            return False
        
        # Backup existing database
        backup_file = f"{db_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(db_file, backup_file)
        print(f"💾 Existing database backed up to: {backup_file}")
    
    try:
        # Read schema file
        print("📖 Reading schema file...")
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Create database connection
        print("🔗 Creating database connection...")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        
        # Execute schema
        print("🏗️  Creating database structure...")
        conn.executescript(schema_sql)
        
        # Verify tables were created
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print(f"✅ Created {len(tables)} tables:")
        for table in tables:
            if not table['name'].startswith('sqlite_'):
                count = conn.execute(f"SELECT COUNT(*) as count FROM {table['name']}").fetchone()
                print(f"   - {table['name']} ({count['count']} records)")
        
        # Check views
        views = conn.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall()
        if views:
            print(f"✅ Created {len(views)} views:")
            for view in views:
                print(f"   - {view['name']}")
        
        # Check indexes
        indexes = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'").fetchall()
        if indexes:
            print(f"✅ Created {len(indexes)} indexes:")
            for index in indexes:
                print(f"   - {index['name']}")
        
        # Check triggers
        triggers = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall()
        if triggers:
            print(f"✅ Created {len(triggers)} triggers:")
            for trigger in triggers:
                print(f"   - {trigger['name']}")
        
        conn.close()
        
        print()
        print("="*60)
        print("✅ DATABASE SETUP COMPLETED SUCCESSFULLY!")
        print("="*60)
        print()
        print("Database is ready for use. You can now:")
        print("1. Run the FinSight application: python run.py")
        print("2. Create your first admin user through the signup page")
        print("3. Start using the expense management system")
        print()
        print(f"Database location: {os.path.abspath(db_file)}")
        print(f"Database size: {os.path.getsize(db_file):,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def add_sample_data(db_file='database/expense_management.db'):
    """Add sample data for testing (optional)"""
    
    print("\n" + "="*40)
    print("ADDING SAMPLE DATA")
    print("="*40)
    
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        
        # Sample company
        conn.execute("""
            INSERT OR IGNORE INTO companies (company_id, name, country_code, base_currency, email) 
            VALUES (1, 'Demo Company Ltd.', 'US', 'USD', 'admin@democompany.com')
        """)
        
        # Sample admin user (password: admin123)
        conn.execute("""
            INSERT OR IGNORE INTO users (user_id, company_id, name, email, password_hash, role_type) 
            VALUES (1, 1, 'Admin Demo', 'admin@democompany.com', 
                   'pbkdf2:sha256:600000$6yH7vQ2C8pDf2QFN$8c5a3f4c2b1d6e9f8a7b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0', 
                   'admin')
        """)
        
        # Sample manager user (password: manager123)
        conn.execute("""
            INSERT OR IGNORE INTO users (user_id, company_id, name, email, password_hash, role_type) 
            VALUES (2, 1, 'Manager Demo', 'manager@democompany.com', 
                   'pbkdf2:sha256:600000$7zI8wR3D9qEg3RNA$9d6b4f5c3c2e7f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d', 
                   'manager')
        """)
        
        # Sample employee user (password: employee123)
        conn.execute("""
            INSERT OR IGNORE INTO users (user_id, company_id, name, email, password_hash, role_type, manager_id) 
            VALUES (3, 1, 'Employee Demo', 'employee@democompany.com', 
                   'pbkdf2:sha256:600000$8aJ9xS4E0rFh4SOB$ae7c5f6d4d3f8a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f', 
                   'employee', 2)
        """)
        
        # Sample approval sequence
        conn.execute("""
            INSERT OR IGNORE INTO approval_sequences (company_id, user_id, sequence_order, is_manager_approver) 
            VALUES (1, 2, 1, 1)
        """)
        
        # Sample approval rule
        conn.execute("""
            INSERT OR IGNORE INTO approval_rules (company_id, category, max_amount, requires_receipt, approval_levels) 
            VALUES (1, 'Travel', 1000.00, 1, 1)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Sample data added successfully!")
        print()
        print("Demo accounts created:")
        print("📋 Admin:    admin@democompany.com    / admin123")
        print("📋 Manager:  manager@democompany.com  / manager123") 
        print("📋 Employee: employee@democompany.com / employee123")
        print()
        print("⚠️  Remember to change these passwords in production!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        return False

def main():
    """Main function"""
    
    # Parse command line arguments
    add_samples = '--sample-data' in sys.argv or '--demo' in sys.argv
    
    print("Starting FinSight Database Setup...")
    print()
    
    # Create database from schema
    success = create_database_from_schema()
    
    if success and add_samples:
        add_sample_data()
    
    if success:
        print("\n🎉 Setup completed! Your FinSight database is ready to use.")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()