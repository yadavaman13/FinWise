# FinSight Deployment Guide

This guide explains how to deploy FinSight to various cloud platforms.

## Quick Deploy Options

### Option 1: Railway (Recommended)
1. Visit [Railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `FinWise` repository
5. Railway will automatically detect and deploy your Flask app
6. Set environment variables in Railway dashboard:
   - `SECRET_KEY`: Generate a secure secret key
   - `FLASK_ENV`: Set to `production`

### Option 2: Render
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

### Option 3: Heroku
1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-finsight-app`
4. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY=your-secure-secret-key
   heroku config:set FLASK_ENV=production
   ```
5. Deploy: `git push heroku main`

## Environment Variables

Required environment variables for production:

- `SECRET_KEY`: A secure random string for Flask sessions
- `FLASK_ENV`: Set to `production` for production mode
- `PORT`: Automatically set by most platforms
- `DATABASE_PATH`: Optional, defaults to `database/expense_management.db`

## Generate Secret Key

To generate a secure secret key, run:
```python
import secrets
print(secrets.token_urlsafe(32))
```

## Post-Deployment Setup

1. Visit your deployed application URL
2. Create an admin account using the signup form
3. The database will be automatically initialized on first run

## Troubleshooting

- If you get import errors, ensure all dependencies are in `requirements.txt`
- For database issues, check that the `database` directory exists
- For file upload issues, verify the `uploads` directory is created
- Check platform logs for detailed error messages

## Files Included for Deployment

- `Procfile`: Defines how to run the application
- `requirements.txt`: Python dependencies
- `runtime.txt`: Python version specification
- `railway.json`: Railway-specific configuration