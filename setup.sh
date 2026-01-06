#!/bin/bash

echo "🚀 Setting up AbdullahHub - Ultimate Plugin Platform"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and setuptools
echo "📥 Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

# Install system dependencies first
echo "📦 Installing system dependencies..."
pip install wheel setuptools

# Install requirements in order
echo "📥 Installing dependencies..."
pip install -r requirements.txt --no-build-isolation

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p storage/databases
mkdir -p storage/uploads
mkdir -p storage/logs
mkdir -p plugins/installed
mkdir -p plugins/temp
mkdir -p plugins/marketplace
mkdir -p static/images

# Set permissions
chmod -R 755 storage
chmod -R 755 plugins

# Initialize database
echo "💾 Initializing database..."
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database created successfully!')
"

# Create admin user
echo "👑 Creating admin user..."
python -c "
from app import app, db
from core.models.user import User
with app.app_context():
    if not User.query.filter_by(email='admin@abdullahhub.com').first():
        admin = User(
            username='admin',
            email='admin@abdullahhub.com',
            is_verified=True,
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created:')
        print('Email: admin@abdullahhub.com')
        print('Password: admin123')
        print('⚠️ Please change the password immediately!')
    else:
        print('Admin user already exists')
"

# Copy environment file
if [ ! -f .env ]; then
    echo "📋 Copying environment template..."
    cp .env.example .env
    echo "✅ Please edit .env file with your configuration"
fi

# Generate secret key
if grep -q "dev-secret-key-change-in-production" .env 2>/dev/null; then
    secret_key=$(python -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/dev-secret-key-change-in-production/$secret_key/" .env
    echo "🔑 Generated secure secret key"
fi

# Create initial plugins
echo "🔌 Creating sample plugins..."
mkdir -p plugins/installed/removebg

# Create simple removebg plugin without complex dependencies
cat > plugins/installed/removebg/plugin.py << 'EOF'
"""
Remove Background Plugin for AbdullahHub
Uses Remove.bg API to remove backgrounds from images
"""

PLUGIN_NAME = "Remove Background"
PLUGIN_DESCRIPTION = "Remove backgrounds from images using AI"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "AbdullahHub"
PLUGIN_CATEGORY = "Image Processing"

import base64
import os

def execute(context):
    """
    Execute the Remove Background plugin
    
    Required in context:
    - api_key: Remove.bg API key
    - input.image: Base64 encoded image or URL
    
    Returns:
    - Base64 encoded image with background removed
    """
    
    api_key = context.get('api_key') or os.environ.get('REMOVEBG_API_KEY')
    if not api_key:
        return {
            "success": False,
            "error": "API key required. Please configure Remove.bg API key in plugin settings."
        }
    
    input_data = context.get('input', {})
    image_data = input_data.get('image')
    
    if not image_data:
        return {
            "success": False,
            "error": "No image provided. Please provide image data or URL."
        }
    
    try:
        # Simulate API call for demo
        # In production, this would call the real API
        return {
            "success": True,
            "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            "format": "png",
            "width": 100,
            "height": 100,
            "credits_charged": "1",
            "message": "Background removed successfully! (Demo mode)"
        }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Processing failed: {str(e)}"
        }
EOF

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run: python app.py"
echo "3. Open: http://localhost:5000"
echo ""
echo "🔑 Admin login:"
echo "   Email: admin@abdullahhub.com"
echo "   Password: admin123"
echo ""
echo "⚠️  Remember to:"
echo "   - Change admin password"
echo "   - Update .env file with your settings"
echo "   - Add your Remove.bg API key: xv5aoeuirxTNZBYS5KykZZEK"
