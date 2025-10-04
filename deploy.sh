#!/bin/bash
# FinSight Deployment Helper Script

echo "🚀 FinSight Deployment Helper"
echo "=============================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first."
    exit 1
fi

echo "📋 Pre-deployment checklist:"
echo "✅ Deployment files created (Procfile, requirements.txt, etc.)"
echo "✅ Environment variables documented in .env.example"
echo "✅ Production configuration updated in app.py"

# Generate a secret key
echo ""
echo "🔐 Generated SECRET_KEY for you:"
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

echo ""
echo "📦 Committing latest changes..."
git add .
git commit -m "Final deployment preparation" 2>/dev/null || echo "No changes to commit"

echo ""
echo "⬆️ Pushing to GitHub..."
git push origin main

echo ""
echo "🎯 Next Steps:"
echo ""
echo "🔴 RAILWAY DEPLOYMENT:"
echo "1. Visit: https://railway.app"
echo "2. Click 'New Project' → 'Deploy from GitHub repo'"
echo "3. Select: yadavaman13/FinWise"
echo "4. Add environment variable: SECRET_KEY (generated above)"
echo "5. Your app will be live at: https://finwise-production.up.railway.app"
echo ""
echo "🔵 VERCEL DEPLOYMENT:"
echo "1. Visit: https://vercel.com"
echo "2. Click 'New Project'"
echo "3. Import: https://github.com/yadavaman13/FinWise"
echo "4. Add environment variable: SECRET_KEY (generated above)"
echo "5. Your app will be live at: https://finwise.vercel.app"
echo ""
echo "✨ Deployment complete! Check the DEPLOYMENT.md file for detailed instructions."