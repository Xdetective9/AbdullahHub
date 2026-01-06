#!/bin/bash

echo "🚀 Deploying AbdullahHub..."

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: AbdullahHub Ultimate Plugin Platform"
fi

# Check deployment platform
if [ "$1" == "render" ]; then
    echo "Deploying to Render..."
    # Render specific steps
    
elif [ "$1" == "railway" ]; then
    echo "Deploying to Railway..."
    # Railway specific steps
    
elif [ "$1" == "replit" ]; then
    echo "Deploying to Replit..."
    # Replit specific steps
    
elif [ "$1" == "heroku" ]; then
    echo "Deploying to Heroku..."
    heroku create abdullahhub-$(date +%s)
    heroku addons:create heroku-postgresql:hobby-dev
    heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    heroku config:set FLASK_ENV=production
    git push heroku main
    
else
    echo "Usage: ./deploy.sh [render|railway|replit|heroku]"
    echo ""
    echo "For manual deployment:"
    echo "1. Push to your GitHub repository"
    echo "2. Connect to your deployment platform"
    echo "3. Set environment variables:"
    echo "   - SECRET_KEY"
    echo "   - DATABASE_URL"
    echo "   - MAIL_USERNAME"
    echo "   - MAIL_PASSWORD"
    echo "   - REMOVEBG_API_KEY"
    echo "4. Deploy!"
fi
