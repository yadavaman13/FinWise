# 🚀 FinSight

A comprehensive, full-stack expense management solution built for modern organizations. Features OCR receipt scanning, multi-currency support, flexible approval workflows, and intelligent automation.

![FinSight](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-lightblue)
![Database](https://img.shields.io/badge/Database-SQLite%2FPostgreSQL-orange)

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Architecture](#-architecture)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### Core Features
- **🔐 Multi-Role Authentication**: Admin, Manager, Employee roles with hierarchical permissions
- **📷 OCR Receipt Scanning**: Automatic data extraction from receipts using Tesseract OCR
- **🌍 Multi-Currency Support**: Real-time currency conversion with API integration
- **🔄 Flexible Approval Workflows**: Sequential, percentage-based, and hybrid approval rules
- **📊 Real-time Dashboard**: Interactive analytics and expense tracking
- **🔍 Advanced Search & Filtering**: Find expenses quickly with smart filters
- **📱 Mobile-Responsive Design**: Works seamlessly on all devices
- **🛡️ Complete Audit Trail**: Full tracking of all system activities

### Advanced Features
- **🤖 AI Policy Compliance**: Automatic violation detection
- **📈 Analytics & Reporting**: Comprehensive expense analytics
- **🔔 Smart Notifications**: Real-time updates and alerts
- **💾 Data Export**: CSV/Excel export functionality
- **🎨 Modern UI/UX**: Clean, intuitive interface with Bootstrap 5
- **⚡ Performance Optimized**: Fast loading and responsive interactions

## 🛠 Tech Stack

### Backend
- **Framework**: Flask 2.3.3
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLite3 with Raw SQL
- **Authentication**: Werkzeug Security
- **File Handling**: PIL (Pillow) for image processing
- **OCR**: Tesseract OCR engine

### Frontend
- **UI Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.0
- **JavaScript**: Vanilla JS with modern ES6+
- **Responsive Design**: Mobile-first approach
- **Charts**: Chart.js (for future analytics)

### APIs & Integrations
- **Currency Exchange**: ExchangeRate-API
- **Country Data**: REST Countries API
- **OCR Processing**: Tesseract OCR
- **Email**: Flask-Mail (for notifications)

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Tesseract OCR engine

### 1-Minute Setup
```bash
# Clone the repository
git clone https://github.com/your-username/expense-management-system.git
cd expense-management-system

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR
# Ubuntu/Debian: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
# Windows: Download from https://github.com/tesseract-ocr/tesseract

# Run the application
python run.py
```

Open your browser and navigate to `http://localhost:5000`

## 🔧 Installation

### Detailed Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/expense-management-system.git
   cd expense-management-system
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract OCR**
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **macOS**: `brew install tesseract`
   - **Windows**: Download from [Tesseract GitHub](https://github.com/tesseract-ocr/tesseract)

5. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

6. **Initialize Database**
   ```bash
   python -c "from app import init_db; init_db()"
   ```

7. **Run Application**
   ```bash
   python run.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///database/expense_management.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Optional API Keys
EXCHANGE_RATE_API_KEY=your_api_key
OCR_API_KEY=your_ocr_api_key
```

### Database Configuration

The system supports both SQLite and PostgreSQL:

```python
# SQLite (Default)
DATABASE = 'sqlite:///database/expense_management.db'

# PostgreSQL (Production)
DATABASE = 'postgresql://user:password@localhost/expense_db'
```

## 📖 Usage

### 1. First Time Setup

1. **Sign Up**: Create your company account
2. **Admin Setup**: First user becomes admin automatically
3. **Add Users**: Create employee and manager accounts
4. **Configure Workflows**: Set up approval rules

### 2. Employee Workflow

1. **Submit Expense**: Upload receipt, system auto-fills details
2. **Track Status**: Monitor approval progress
3. **View History**: Access all past expenses

### 3. Manager Workflow

1. **Review Expenses**: Approve/reject team submissions
2. **Add Comments**: Provide feedback on decisions
3. **Monitor Team**: Track team spending patterns

### 4. Admin Functions

1. **User Management**: Add/edit/deactivate users
2. **Approval Rules**: Configure workflow logic
3. **System Monitoring**: Access audit logs and analytics

## 📚 API Documentation

### Authentication Endpoints

```http
POST /api/login
POST /api/logout
POST /api/signup
```

### Expense Management

```http
GET /api/expenses
POST /api/expenses
PUT /api/expenses/{id}
DELETE /api/expenses/{id}
```

### Approval System

```http
GET /api/approvals
POST /api/approvals/{id}/approve
POST /api/approvals/{id}/reject
```

### User Management

```http
GET /api/users
POST /api/users
PUT /api/users/{id}
DELETE /api/users/{id}
```

## 🏗 Architecture

### System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend     │    │    Database     │
│   (Bootstrap)   │◄──►│     (Flask)     │◄──►│    (SQLite)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  External APIs  │
                    │  • Exchange Rate│
                    │  • OCR Service  │
                    │  • Countries    │
                    └─────────────────┘
```

### Database Schema

```sql
-- Core Tables
companies (company_id, name, country_code, base_currency)
users (user_id, company_id, name, email, role_type, manager_id)
expense_claims (claim_id, user_id, amount, status, receipt_url)
approvals (approval_id, claim_id, approver_id, decision)
approval_rules (rule_id, company_id, rule_type, threshold)
audit_log (log_id, user_id, action, entity, timestamp)
```

## 📦 Deployment

### Production Deployment

1. **Docker Deployment**
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
   ```

2. **Environment Setup**
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:pass@localhost/db
   ```

3. **Web Server Configuration**
   - Nginx reverse proxy
   - SSL certificate
   - Static file serving

### Scaling Considerations

- **Database**: PostgreSQL for production
- **File Storage**: AWS S3 or similar
- **Caching**: Redis for session storage
- **Load Balancing**: Multiple Flask instances

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

### Development Setup

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flask team for the excellent framework
- Bootstrap team for the UI components
- Tesseract OCR for text recognition
- All contributors and testers

## 📞 Support

- **Documentation**: [Wiki](https://github.com/your-repo/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: support@finsight.com

---

**Built with ❤️ for efficient expense management**
