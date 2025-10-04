import os
import time
import threading
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import sqlite3
import requests
import json
from PIL import Image
import pytesseract
import re
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'expense_management_secret_key_2024')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-size

# Database configuration
DATABASE = os.environ.get('DATABASE_PATH', 'database/expense_management.db')

def init_db():
    """Initialize the database with all required tables"""
    # Create necessary directories
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create companies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country_code TEXT,
            base_currency TEXT DEFAULT 'USD',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role_type TEXT CHECK (role_type IN ('admin','manager','employee')) DEFAULT 'employee',
            manager_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(company_id),
            FOREIGN KEY (manager_id) REFERENCES users(user_id)
        )
    """)

    # Create expense_claims table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_claims (
            claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            company_id INTEGER,
            title TEXT,
            category TEXT,
            description TEXT,
            amount DECIMAL(12,2),
            currency TEXT DEFAULT 'USD',
            converted_amount DECIMAL(12,2),
            expense_date DATE,
            status TEXT CHECK (status IN ('pending','approved','rejected','processing')) DEFAULT 'pending',
            receipt_url TEXT,
            receipt_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (company_id) REFERENCES companies(company_id)
        )
    """)

    # Create approvals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id INTEGER,
            approver_id INTEGER,
            sequence_order INTEGER DEFAULT 1,
            decision TEXT CHECK (decision IN ('approved','rejected','pending')) DEFAULT 'pending',
            comment TEXT,
            decided_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (claim_id) REFERENCES expense_claims(claim_id),
            FOREIGN KEY (approver_id) REFERENCES users(user_id)
        )
    """)

    # Create approval_rules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approval_rules (
            rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            rule_name TEXT,
            rule_type TEXT CHECK (rule_type IN ('percentage','specific','hybrid','sequential')),
            threshold DECIMAL(5,2),
            specific_user_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(company_id),
            FOREIGN KEY (specific_user_id) REFERENCES users(user_id)
        )
    """)

    # Create approval_sequences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approval_sequences (
            sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            user_id INTEGER,
            sequence_order INTEGER,
            is_manager_approver BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(company_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Create audit_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            entity TEXT,
            entity_id INTEGER,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()

    
    # Setup default approval sequences
    setup_default_approval_sequences()

def setup_default_approval_sequences():
    """Setup default approval sequences for companies that don't have any"""
    conn = get_db_connection()
    
    # Get all companies
    companies = conn.execute('SELECT company_id FROM companies').fetchall()
    
    for company in companies:
        company_id = company['company_id']
        
        # Check if company already has approval sequences
        existing_sequences = conn.execute("""
            SELECT COUNT(*) as count FROM approval_sequences WHERE company_id = ?
        """, (company_id,)).fetchone()
        
        if existing_sequences['count'] == 0:
            # No sequences exist, create default ones
            # Get all admins in the company (excluding the first admin who might be submitting)
            admins = conn.execute("""
                SELECT user_id FROM users 
                WHERE company_id = ? AND role_type = 'admin' AND is_active = 1
                ORDER BY user_id
            """, (company_id,)).fetchall()
            
            # Get all managers in the company
            managers = conn.execute("""
                SELECT user_id FROM users 
                WHERE company_id = ? AND role_type = 'manager' AND is_active = 1
                ORDER BY user_id
            """, (company_id,)).fetchall()
            
            sequence_order = 1
            
            # Add managers first
            for manager in managers:
                conn.execute("""
                    INSERT INTO approval_sequences (company_id, user_id, sequence_order, is_manager_approver)
                    VALUES (?, ?, ?, 1)
                """, (company_id, manager['user_id'], sequence_order))
                sequence_order += 1
            
            # Add admins after managers
            for admin in admins:
                conn.execute("""
                    INSERT INTO approval_sequences (company_id, user_id, sequence_order, is_manager_approver)
                    VALUES (?, ?, ?, 0)
                """, (company_id, admin['user_id'], sequence_order))
                sequence_order += 1
    
    conn.commit()
    conn.close()

# Thread-local storage for database connections
thread_local = threading.local()

import threading
from contextlib import contextmanager

# Thread-safe database connection manager
class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.local = threading.local()
        self._lock = threading.RLock()
    
    def get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self.local, 'connection') or self.local.connection is None:
            with self._lock:
                self.local.connection = sqlite3.connect(
                    self.db_path, 
                    timeout=120.0,
                    check_same_thread=False
                )
                self.local.connection.row_factory = sqlite3.Row
                # Optimize for concurrency
                self.local.connection.execute('PRAGMA journal_mode=WAL;')
                self.local.connection.execute('PRAGMA synchronous=NORMAL;')
                self.local.connection.execute('PRAGMA cache_size=2000;')
                self.local.connection.execute('PRAGMA temp_store=memory;')
                self.local.connection.execute('PRAGMA busy_timeout=120000;')
                self.local.connection.execute('PRAGMA wal_autocheckpoint=1000;')
        return self.local.connection
    
    def close_connection(self):
        """Close thread-local connection"""
        if hasattr(self.local, 'connection') and self.local.connection:
            self.local.connection.close()
            self.local.connection = None

# Initialize database manager
db_manager = DatabaseManager(DATABASE)

def get_db():
    """Get database connection - simplified version"""
    return db_manager.get_connection()

def get_db_connection():
    """Get a fresh database connection (for non-request contexts)"""
    return db_manager.get_connection()

@contextmanager
def database_transaction():
    """Context manager for database transactions with retry logic"""
    max_retries = 5
    for attempt in range(max_retries):
        conn = None
        try:
            conn = db_manager.get_connection()
            yield conn
            conn.commit()
            break
        except sqlite3.OperationalError as e:
            if conn:
                conn.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.2 * (2 ** attempt))  # Exponential backoff
                continue
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            raise

def execute_db_operation(operation_func, *args, **kwargs):
    """Execute database operation with automatic retry and connection management"""
    with database_transaction() as conn:
        return operation_func(conn, *args, **kwargs)
            

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role_type') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Flask teardown handler
@app.teardown_appcontext
def close_db_connection(error):
    """Close database connection when app context tears down"""
    db_manager.close_connection()

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)

# Utility functions
def get_currency_rates(base_currency='USD'):
    """Get currency conversion rates"""
    try:
        response = requests.get(f'https://api.exchangerate-api.com/v4/latest/{base_currency}')
        if response.status_code == 200:
            return response.json()['rates']
    except:
        pass
    return {}

def get_countries_currencies():
    """Get list of countries and their currencies"""
    try:
        response = requests.get('https://restcountries.com/v3.1/all?fields=name,currencies')
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

def convert_currency(amount, from_currency, to_currency):
    """Convert currency amount"""
    if from_currency == to_currency:
        return amount

    rates = get_currency_rates(from_currency)
    if to_currency in rates:
        return round(amount * rates[to_currency], 2)
    return amount

def ocr_receipt(image_path):
    """Extract text from receipt using OCR"""
    try:
        # Open image and extract text
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)

        # Extract information using regex patterns
        amount_pattern = r'[\$€£¥₹]?(\d+\.?\d*)'
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'

        amounts = re.findall(amount_pattern, text)
        dates = re.findall(date_pattern, text)

        # Find the largest amount (likely the total)
        total_amount = 0
        if amounts:
            total_amount = max([float(amt) for amt in amounts if amt])

        # Get first date found
        expense_date = datetime.now().strftime('%Y-%m-%d')
        if dates:
            try:
                # Try to parse the date
                date_str = dates[0]
                if '/' in date_str:
                    expense_date = datetime.strptime(date_str, '%m/%d/%Y').strftime('%Y-%m-%d')
                elif '-' in date_str:
                    expense_date = datetime.strptime(date_str, '%m-%d-%Y').strftime('%Y-%m-%d')
            except:
                pass

        return {
            'amount': total_amount,
            'date': expense_date,
            'description': text[:200],  # First 200 chars as description
            'raw_text': text
        }
    except Exception as e:
        return {
            'amount': 0,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'description': 'OCR processing failed',
            'raw_text': str(e)
        }

def log_audit(user_id, action, entity, entity_id, details=''):
    """Log audit trail"""
    def _log_audit(conn, user_id, action, entity, entity_id, details):
        conn.execute("""
            INSERT INTO audit_log (user_id, action, entity, entity_id, details)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, action, entity, entity_id, details))
    
    execute_db_operation(_log_audit, user_id, action, entity, entity_id, details)


# Routes
@app.route('/')
def index():
    """Home page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup with company creation"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        company_name = request.form['company_name']
        country_code = request.form['country_code']

        # Get currency for selected country
        base_currency = 'USD'  # Default
        countries = get_countries_currencies()
        for country in countries:
            if country.get('name', {}).get('common') == country_code:
                currencies = country.get('currencies', {})
                if currencies:
                    base_currency = list(currencies.keys())[0]
                break

        conn = get_db()

        # Check if email already exists
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('signup.html', countries=countries)

        # Check if company already exists
        existing_company = conn.execute('SELECT * FROM companies WHERE name = ? AND country_code = ?', 
                                      (company_name, country_code)).fetchone()
        
        if existing_company:
            # Company exists, add user as employee
            company_id = existing_company['company_id']
            base_currency = existing_company['base_currency']
            role_type = 'employee'  # Default role for joining existing company
            
            password_hash = generate_password_hash(password)
            cursor = conn.execute("""
                INSERT INTO users (company_id, name, email, password_hash, role_type)
                VALUES (?, ?, ?, ?, ?)
            """, (company_id, name, email, password_hash, role_type))
            user_id = cursor.lastrowid
            
            flash('Account created successfully! You have been added as an employee.', 'success')
        else:
            # Create new company
            cursor = conn.execute("""
                INSERT INTO companies (name, country_code, base_currency)
                VALUES (?, ?, ?)
            """, (company_name, country_code, base_currency))
            company_id = cursor.lastrowid

            # Create admin user (first user of the company)
            password_hash = generate_password_hash(password)
            role_type = 'admin'
            cursor = conn.execute("""
                INSERT INTO users (company_id, name, email, password_hash, role_type)
                VALUES (?, ?, ?, ?, ?)
            """, (company_id, name, email, password_hash, role_type))
            user_id = cursor.lastrowid
            
            flash('Company and admin account created successfully!', 'success')

        conn.commit()
    

        # Log user in
        session['user_id'] = user_id
        session['company_id'] = company_id
        session['name'] = name
        session['role_type'] = role_type
        session['base_currency'] = base_currency

        if role_type == 'admin':
            log_audit(user_id, 'CREATE', 'COMPANY', company_id, f'Company created: {company_name}')
        else:
            log_audit(user_id, 'JOIN', 'COMPANY', company_id, f'Joined company: {company_name}')

        return redirect(url_for('dashboard'))

    countries = get_countries_currencies()
    return render_template('signup.html', countries=countries)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        user = conn.execute("""
            SELECT u.*, c.base_currency 
            FROM users u 
            JOIN companies c ON u.company_id = c.company_id 
            WHERE u.email = ? AND u.is_active = 1
        """, (email,)).fetchone()
    

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['company_id'] = user['company_id']
            session['name'] = user['name']
            session['role_type'] = user['role_type']
            session['base_currency'] = user['base_currency']

            log_audit(user['user_id'], 'LOGIN', 'USER', user['user_id'])

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    if 'user_id' in session:
        log_audit(session['user_id'], 'LOGOUT', 'USER', session['user_id'])
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    conn = get_db()

    # Get user's expense statistics
    user_stats = conn.execute("""
        SELECT 
            COUNT(*) as total_claims,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_claims,
            COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_claims,
            COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_claims,
            COALESCE(SUM(CASE WHEN status = 'approved' THEN converted_amount ELSE 0 END), 0) as total_approved
        FROM expense_claims 
        WHERE user_id = ?
    """, (session['user_id'],)).fetchone()

    # Get recent expenses
    recent_expenses = conn.execute("""
        SELECT * FROM expense_claims 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 5
    """, (session['user_id'],)).fetchall()

    # Get pending approvals (for managers/admins)
    pending_approvals = []
    if session['role_type'] in ['admin', 'manager']:
        pending_approvals = conn.execute("""
            SELECT ec.*, u.name as employee_name, a.sequence_order
            FROM expense_claims ec
            JOIN users u ON ec.user_id = u.user_id
            JOIN approvals a ON ec.claim_id = a.claim_id
            WHERE a.approver_id = ? AND a.decision = 'pending'
            ORDER BY ec.created_at DESC
        """, (session['user_id'],)).fetchall()



    return render_template('dashboard.html', 
                         user_stats=user_stats, 
                         recent_expenses=recent_expenses,
                         pending_approvals=pending_approvals)

@app.route('/submit_expense', methods=['GET', 'POST'])
@login_required
def submit_expense():
    """Submit new expense claim"""
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        description = request.form['description']
        amount = float(request.form['amount'])
        currency = request.form['currency']
        expense_date = request.form['expense_date']

        # Handle file upload
        receipt_url = None
        receipt_data = None

        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                receipt_url = filename

                # Perform OCR on the receipt
                ocr_data = ocr_receipt(file_path)
                receipt_data = json.dumps(ocr_data)

        # Convert currency to company base currency
        base_currency = session['base_currency']
        converted_amount = convert_currency(amount, currency, base_currency)

        # Create expense claim using thread-safe transaction
        with database_transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO expense_claims (user_id, company_id, title, category, description, 
                                          amount, currency, converted_amount, expense_date, 
                                          receipt_url, receipt_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session['user_id'], session['company_id'], title, category, description,
                   amount, currency, converted_amount, expense_date, receipt_url, receipt_data))

            claim_id = cursor.lastrowid

            # Create approval workflow
            create_approval_workflow(claim_id, session['user_id'], session['company_id'])
    

        log_audit(session['user_id'], 'CREATE', 'EXPENSE_CLAIM', claim_id, 
                 f'Expense claim created: {title}')

        flash('Expense claim submitted successfully!', 'success')
        return redirect(url_for('my_expenses'))

    # Get available currencies
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'INR', 'CAD', 'AUD', 'CHF']
    categories = ['Travel', 'Meals', 'Office Supplies', 'Transportation', 'Accommodation', 'Other']

    return render_template('submit_expense.html', currencies=currencies, categories=categories)

@app.route('/my_expenses')
@login_required
def my_expenses():
    """View user's expense claims"""
    conn = get_db()
    expenses = conn.execute("""
        SELECT * FROM expense_claims 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (session['user_id'],)).fetchall()


    return render_template('my_expenses.html', expenses=expenses)

@app.route('/approvals')
@login_required
def approvals():
    """View pending approvals for managers/admins"""
    if session['role_type'] not in ['admin', 'manager']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db()
    pending_approvals = conn.execute("""
        SELECT ec.*, u.name as employee_name, a.sequence_order, a.approval_id
        FROM expense_claims ec
        JOIN users u ON ec.user_id = u.user_id
        JOIN approvals a ON ec.claim_id = a.claim_id
        WHERE a.approver_id = ? AND a.decision = 'pending'
        ORDER BY ec.created_at DESC
    """, (session['user_id'],)).fetchall()


    return render_template('approvals.html', pending_approvals=pending_approvals)

@app.route('/approve_expense/<int:approval_id>', methods=['POST'])
@login_required
def approve_expense(approval_id):
    """Approve or reject expense"""
    decision = request.form['decision']
    comment = request.form.get('comment', '')

    conn = get_db()

    # Update approval
    conn.execute("""
        UPDATE approvals 
        SET decision = ?, comment = ?, decided_at = CURRENT_TIMESTAMP
        WHERE approval_id = ? AND approver_id = ?
    """, (decision, comment, approval_id, session['user_id']))

    # Get claim information
    approval = conn.execute("""
        SELECT * FROM approvals WHERE approval_id = ?
    """, (approval_id,)).fetchone()

    if approval:
        # Check if this completes the approval process
        process_approval_workflow(approval['claim_id'], decision)

    conn.commit()


    log_audit(session['user_id'], decision.upper(), 'EXPENSE_APPROVAL', approval_id, comment)

    flash(f'Expense {decision} successfully!', 'success')
    return redirect(url_for('approvals'))

@app.route('/admin')
@admin_required
def admin_panel():
    """Admin panel"""
    conn = get_db()

    # Get company statistics
    stats = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM users WHERE company_id = ? AND is_active = 1) as total_users,
            (SELECT COUNT(*) FROM expense_claims WHERE company_id = ?) as total_claims,
            (SELECT COALESCE(SUM(converted_amount), 0) FROM expense_claims WHERE company_id = ? AND status = 'approved') as total_approved_amount
    """, (session['company_id'], session['company_id'], session['company_id'])).fetchone()

    # Get recent activities
    activities = conn.execute("""
        SELECT al.*, u.name as user_name
        FROM audit_log al
        JOIN users u ON al.user_id = u.user_id
        WHERE u.company_id = ?
        ORDER BY al.timestamp DESC
        LIMIT 20
    """, (session['company_id'],)).fetchall()



    return render_template('admin.html', stats=stats, activities=activities)

@app.route('/manage_users')
@admin_required
def manage_users():
    """Manage users"""
    conn = get_db()
    users = conn.execute("""
        SELECT u.*, m.name as manager_name
        FROM users u
        LEFT JOIN users m ON u.manager_id = m.user_id
        WHERE u.company_id = ?
        ORDER BY u.role_type, u.name
    """, (session['company_id'],)).fetchall()


    return render_template('manage_users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    """Add new user"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role_type = request.form['role_type']
        manager_id = request.form.get('manager_id') or None

        conn = get_db()

        # Check if email already exists
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            flash('Email already exists', 'error')
            return redirect(url_for('add_user'))

        # Create user
        password_hash = generate_password_hash(password)
        cursor = conn.execute("""
            INSERT INTO users (company_id, name, email, password_hash, role_type, manager_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session['company_id'], name, email, password_hash, role_type, manager_id))

        user_id = cursor.lastrowid
        conn.commit()
    

        log_audit(session['user_id'], 'CREATE', 'USER', user_id, f'User created: {name}')

        flash('User added successfully!', 'success')
        return redirect(url_for('manage_users'))

    # Get managers for dropdown
    conn = get_db()
    managers = conn.execute("""
        SELECT user_id, name FROM users 
        WHERE company_id = ? AND role_type IN ('admin', 'manager') AND is_active = 1
    """, (session['company_id'],)).fetchall()


    return render_template('add_user.html', managers=managers)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit existing user"""
    conn = get_db()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role_type = request.form['role_type']
        manager_id = request.form.get('manager_id') or None
        is_active = 1 if request.form.get('is_active') else 0
        
        # Check if email already exists for other users
        existing_user = conn.execute("""
            SELECT * FROM users WHERE email = ? AND user_id != ?
        """, (email, user_id)).fetchone()
        
        if existing_user:
            flash('Email already exists for another user', 'error')
            return redirect(url_for('edit_user', user_id=user_id))
        
        # Update user
        conn.execute("""
            UPDATE users 
            SET name = ?, email = ?, role_type = ?, manager_id = ?, is_active = ?
            WHERE user_id = ? AND company_id = ?
        """, (name, email, role_type, manager_id, is_active, user_id, session['company_id']))
        
        conn.commit()
    
        
        log_audit(session['user_id'], 'UPDATE', 'USER', user_id, f'User updated: {name}')
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('manage_users'))
    
    # GET request - show edit form
    user = conn.execute("""
        SELECT * FROM users WHERE user_id = ? AND company_id = ?
    """, (user_id, session['company_id'])).fetchone()
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('manage_users'))
    
    # Get potential managers (admins and managers, excluding the user being edited)
    managers = conn.execute("""
        SELECT user_id, name FROM users 
        WHERE company_id = ? AND role_type IN ('admin', 'manager') 
        AND is_active = 1 AND user_id != ?
    """, (session['company_id'], user_id)).fetchall()
    

    
    return render_template('edit_user.html', user=user, managers=managers)

def create_approval_workflow(claim_id, user_id, company_id):
    """Create approval workflow for expense claim with robust fallback logic"""
    def _create_workflow(conn, claim_id, user_id, company_id):
        # Get user's manager
        user = conn.execute('SELECT manager_id FROM users WHERE user_id = ?', (user_id,)).fetchone()

        # Get approval sequences for the company
        sequences = conn.execute("""
            SELECT * FROM approval_sequences 
            WHERE company_id = ? 
            ORDER BY sequence_order
        """, (company_id,)).fetchall()

        approvers = []
        current_sequence = 1

        # Strategy 1: Add manager as first approver if exists
        if user and user['manager_id']:
            # Verify manager is active and has manager/admin role
            manager = conn.execute("""
                SELECT user_id, role_type FROM users 
                WHERE user_id = ? AND is_active = 1 AND role_type IN ('manager', 'admin')
            """, (user['manager_id'],)).fetchone()
            
            if manager:
                approvers.append({
                    'approver_id': manager['user_id'],
                    'sequence_order': current_sequence
                })
                current_sequence += 1

        # Strategy 2: Add sequence approvers
        for seq in sequences:
            if seq['is_manager_approver'] and user and user['manager_id']:
                continue  # Skip if manager already added

            # Verify sequence approver is active and has appropriate role
            seq_approver = conn.execute("""
                SELECT user_id FROM users 
                WHERE user_id = ? AND is_active = 1 AND role_type IN ('manager', 'admin')
            """, (seq['user_id'],)).fetchone()
            
            if seq_approver:
                approvers.append({
                    'approver_id': seq['user_id'],
                    'sequence_order': current_sequence
                })
                current_sequence += 1

        # Strategy 3: Fallback - if no approvers found, assign to company admins
        if not approvers:
            company_admins = conn.execute("""
                SELECT user_id FROM users 
                WHERE company_id = ? AND role_type = 'admin' AND is_active = 1 AND user_id != ?
                ORDER BY user_id
            """, (company_id, user_id)).fetchall()
            
            for admin in company_admins:
                approvers.append({
                    'approver_id': admin['user_id'],
                    'sequence_order': current_sequence
                })
                current_sequence += 1

        # Strategy 4: Last resort - if still no approvers, assign to any admin in the company
        if not approvers:
            any_admin = conn.execute("""
                SELECT user_id FROM users 
                WHERE company_id = ? AND role_type = 'admin' AND is_active = 1
                ORDER BY user_id LIMIT 1
            """, (company_id,)).fetchone()
            
            if any_admin:
                approvers.append({
                    'approver_id': any_admin['user_id'],
                    'sequence_order': 1
                })

        # Create approval records
        for approver in approvers:
            conn.execute("""
                INSERT INTO approvals (claim_id, approver_id, sequence_order)
                VALUES (?, ?, ?)
            """, (claim_id, approver['approver_id'], approver['sequence_order']))

        return len(approvers)

    # Execute the workflow creation
    approver_count = execute_db_operation(_create_workflow, claim_id, user_id, company_id)
    
    # Log approval workflow creation (after successful transaction)
    log_audit(user_id, 'CREATE', 'APPROVAL_WORKFLOW', claim_id, f'Created approval workflow with {approver_count} approvers')

def process_approval_workflow(claim_id, decision):
    """Process approval workflow logic"""
    def _process_workflow(conn, claim_id, decision):
        # Get all approvals for this claim
        approvals = conn.execute("""
            SELECT * FROM approvals 
            WHERE claim_id = ? 
            ORDER BY sequence_order
        """, (claim_id,)).fetchall()

        # Check if claim should be approved/rejected
        if decision == 'rejected':
            # If any approval is rejected, reject the entire claim
            conn.execute("""
                UPDATE expense_claims 
                SET status = 'rejected' 
                WHERE claim_id = ?
            """, (claim_id,))
        else:
            # Check if all required approvals are complete
            pending_approvals = [a for a in approvals if a['decision'] == 'pending']

            if not pending_approvals:
                # All approvals complete, approve the claim
                conn.execute("""
                    UPDATE expense_claims 
                    SET status = 'approved' 
                    WHERE claim_id = ?
                """, (claim_id,))

    # Execute the workflow processing
    execute_db_operation(_process_workflow, claim_id, decision)

@app.route('/upload_receipt', methods=['POST'])
@login_required
def upload_receipt():
    """Handle OCR receipt upload via AJAX"""
    if 'receipt' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    file = request.files['receipt']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})

    if file:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Perform OCR
        ocr_data = ocr_receipt(file_path)

        return jsonify({
            'success': True,
            'data': ocr_data,
            'filename': filename
        })

    return jsonify({'error': 'Upload failed'})
