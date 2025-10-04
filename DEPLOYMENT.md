# FinSight Deployment Guide

This guide explains how to deploy FinSight to various cloud platforms.

## 🚀 Quick Deploy Options

### Option 1: Railway (Recommended for Full-Stack Apps)

**One-Click Deploy:**
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-url)

**Manual Deploy:**
1. Visit [Railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `yadavaman13/FinWise` repository
5. Railway will automatically:
   - Detect your Flask application
   - Install dependencies from `requirements.txt`
   - Use the `Procfile` for startup command
   - Assign a public URL
6. Set environment variables in Railway dashboard:
   - `SECRET_KEY`: Generate a secure secret key (see below)
   - `FLASK_ENV`: Set to `production`

**Railway Features:**
- ✅ Automatic HTTPS
- ✅ Custom domains
- ✅ PostgreSQL/MySQL databases available
- ✅ File storage persistence
- ✅ Git-based deployments

### Option 2: Vercel (Serverless)

**One-Click Deploy:**
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yadavaman13/FinWise)

**Manual Deploy:**
1. Visit [Vercel.com](https://vercel.com)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Import your `yadavaman13/FinWise` repository
5. Vercel will automatically:
   - Detect the Flask app via `vercel.json`
   - Use Python runtime
   - Deploy as serverless functions
6. Add environment variables in Vercel dashboard:
   - `SECRET_KEY`: Generate a secure secret key
   - `FLASK_ENV`: `production`

**Vercel Features:**
- ✅ Global CDN
- ✅ Automatic HTTPS
- ✅ Serverless architecture
- ✅ Fast cold starts
- ⚠️ Stateless (database resets on each deploy)

### Option 3: Render
1. Visit [Render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click "New" → "Web Service"
4. Connect your `FinWise` repository
5. Use these settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Environment: `Python 3`
6. Add environment variables:
   - `SECRET_KEY`: Generate a secure secret key
   - `FLASK_ENV`: `production`

### Option 4: Heroku
1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-finsight-app`
4. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY=your-secure-secret-key
   heroku config:set FLASK_ENV=production
   ```
5. Deploy: `git push heroku main`

## 🔧 Platform-Specific Instructions

### Railway Deployment Steps
```bash
# 1. Ensure your code is pushed to GitHub
git add .
git commit -m "Prepare for Railway deployment"
git push origin main

# 2. Visit Railway.app and connect your GitHub repo
# 3. Railway will automatically use these files:
#    - requirements.txt (dependencies)
#    - Procfile (startup command)
#    - railway.json (configuration)
```

### Vercel Deployment Steps
```bash
# 1. Install Vercel CLI (optional)
npm i -g vercel

# 2. Deploy directly from GitHub or use CLI
vercel --prod

# Vercel uses these files:
# - vercel.json (configuration)
# - index.py (entry point)
# - requirements.txt (dependencies)
```

## 🔐 Environment Variables

Required environment variables for production:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Secure random string for Flask sessions | `your-super-secret-key-here` |
| `FLASK_ENV` | Environment mode | `production` |
| `PORT` | Server port (auto-set by platforms) | `8000` |
| `DATABASE_PATH` | SQLite database path (optional) | `database/expense_management.db` |

### Generate Secret Key

To generate a secure secret key:

**Method 1: Python**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**Method 2: Online**
Visit [Generate Secret Key](https://flask.palletsprojects.com/en/2.3.x/config/#SECRET_KEY) or use any secure random string generator.

## 🚀 Post-Deployment Setup

1. **Visit your deployed application URL**
   - Railway: `https://your-app-name.up.railway.app`
   - Vercel: `https://your-repo-name.vercel.app`

2. **Create admin account**
   - Click "Sign Up" 
   - Fill in admin details
   - The first user becomes admin automatically

3. **Initialize sample data (optional)**
   - The database initializes automatically
   - You can add sample companies and users via the admin panel

## 🐛 Troubleshooting

### Common Issues

**Import Errors:**
- Ensure all dependencies are in `requirements.txt`
- Check Python version compatibility in `runtime.txt`

**Database Issues:**
- Verify database directory creation in `init_db()`
- Check file permissions for SQLite database

**File Upload Problems:**
- Ensure `uploads` directory exists and is writable
- Verify `MAX_CONTENT_LENGTH` setting

**Environment Variables:**
- Double-check all required env vars are set
- Verify secret key is properly generated

### Platform-Specific Issues

**Railway:**
- Check Railway logs in dashboard
- Verify Procfile syntax
- Ensure PORT environment variable usage

**Vercel:**
- Serverless functions have execution time limits
- Database persists only during request lifecycle
- Check Vercel function logs

## 📁 Deployment Files Reference

| File | Purpose | Platform |
|------|---------|----------|
| `Procfile` | Application startup command | Railway, Heroku |
| `requirements.txt` | Python dependencies | All platforms |
| `runtime.txt` | Python version | Railway, Heroku |
| `vercel.json` | Vercel configuration | Vercel |
| `railway.json` | Railway configuration | Railway |
| `index.py` | Vercel entry point | Vercel |
| `.env.example` | Environment variables template | All platforms |

## 🔗 Live Demo URLs (After Deployment)

After successful deployment, your FinSight application will be available at:

- **Railway**: `https://finwise-production.up.railway.app`
- **Vercel**: `https://finwise.vercel.app`
- **Custom Domain**: Configure in platform dashboard