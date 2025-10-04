#!/usr/bin/env python3
"""
FinSight Database Checker
A simple script to check and display database contents
"""

import sqlite3
import os
from datetime import datetime

def check_database():
    """Check database structure and contents"""
    db_path = 'database/expense_management.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        print(f"Expected location: {os.path.abspath(db_path)}")
        return False
    
    print("="*60)
    print("         FINSIGHT DATABASE CHECKER")
    print("="*60)
    print(f"📍 Database: {db_path}")
    print(f"📊 Size: {os.path.getsize(db_path):,} bytes")
    print(f"🕐 Last Modified: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get database schema
        print("\n" + "="*40)
        print("DATABASE TABLES")
        print("="*40)
        
        tables = conn.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()
        
        for table in tables:
            # Get row count
            count = conn.execute(f"SELECT COUNT(*) as count FROM {table['name']}").fetchone()
            print(f"📋 {table['name']:20} ({count['count']:3} records)")
        
        # Show company information
        print("\n" + "="*40)
        print("COMPANIES")
        print("="*40)
        
        companies = conn.execute("""
            SELECT company_id, name, country_code, base_currency 
            FROM companies ORDER BY company_id
        """).fetchall()
        
        if companies:
            for c in companies:
                print(f"🏢 [{c['company_id']:2}] {c['name']:<20} | {c['country_code']} | {c['base_currency']}")
        else:
            print("No companies found")
        
        # Show user information
        print("\n" + "="*40)
        print("USERS")
        print("="*40)
        
        users = conn.execute("""
            SELECT u.user_id, u.name, u.email, u.role_type, u.is_active,
                   c.name as company_name, m.name as manager_name
            FROM users u
            LEFT JOIN companies c ON u.company_id = c.company_id
            LEFT JOIN users m ON u.manager_id = m.user_id
            ORDER BY u.user_id
        """).fetchall()
        
        if users:
            for u in users:
                status = "✅" if u['is_active'] else "❌"
                manager = f"👨‍💼 {u['manager_name']}" if u['manager_name'] else "No Manager"
                print(f"{status} [{u['user_id']:2}] {u['name']:<18} | {u['role_type']:<8} | {u['company_name']:<15} | {manager}")
        else:
            print("No users found")
        
        # Show recent expenses
        print("\n" + "="*40)
        print("RECENT EXPENSES (Last 5)")
        print("="*40)
        
        expenses = conn.execute("""
            SELECT ec.claim_id, ec.title, ec.amount, ec.currency, ec.status,
                   u.name as user_name, ec.created_at
            FROM expense_claims ec
            JOIN users u ON ec.user_id = u.user_id
            ORDER BY ec.created_at DESC
            LIMIT 5
        """).fetchall()
        
        if expenses:
            for e in expenses:
                status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(e['status'], "❓")
                print(f"{status_emoji} [{e['claim_id']:2}] {e['title']:<20} | ${e['amount']:>8} {e['currency']} | {e['user_name']}")
        else:
            print("No expenses found")
        
        # Show pending approvals
        print("\n" + "="*40)
        print("PENDING APPROVALS")
        print("="*40)
        
        pending = conn.execute("""
            SELECT a.approval_id, ec.title, ec.amount, ec.currency,
                   u1.name as employee_name, u2.name as approver_name,
                   a.sequence_order, ec.status
            FROM approvals a
            JOIN expense_claims ec ON a.claim_id = ec.claim_id
            JOIN users u1 ON ec.user_id = u1.user_id
            JOIN users u2 ON a.approver_id = u2.user_id
            WHERE ec.status = 'pending'
            ORDER BY a.approval_id
        """).fetchall()
        
        if pending:
            for p in pending:
                print(f"⏳ {p['title']:<20} | ${p['amount']:>8} {p['currency']} | {p['employee_name']} → {p['approver_name']}")
        else:
            print("No pending approvals")
        
        conn.close()
        print("\n" + "="*60)
        print("✅ Database check completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    print("Starting FinSight Database Check...")
    success = check_database()
    exit(0 if success else 1)