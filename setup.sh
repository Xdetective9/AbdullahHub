#!/bin/bash

echo "🚀 Setting up AbdullahHub - Ultimate Plugin Platform"

# Check if Python 3.11 is installed
if ! command -v python3.11 &> /dev/null; then
    echo "⚠️  Python 3.11 not found. Please install Python 3.11 first."
    echo "For Ubuntu/Debian: sudo apt install python3.11 python3.11-venv"
    echo "For macOS: brew install python@3.11"
    exit 1
fi

# Create virtual environment with Python 3.11
echo "📦 Creating virtual environment with Python 3.11..."
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p storage/databases
mkdir -p storage/uploads
mkdir -p storage/logs
mkdir -p plugins/installed
mkdir -p plugins/temp
mkdir -p plugins/marketplace
mkdir -p static/images
mkdir -p templates/emails
mkdir -p templates/admin
mkdir -p templates/auth
mkdir -p templates/plugins
mkdir -p templates/errors

# Set permissions
chmod -R 755 storage
chmod -R 755 plugins

# Copy template files if they don't exist
if [ ! -f .env ]; then
    echo "📋 Copying environment template..."
    cp .env.example .env
    echo "✅ Please edit .env file with your configuration"
fi

# Generate secret key if not set
if grep -q "dev-secret-key-change-in-production" .env 2>/dev/null; then
    secret_key=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i.bak "s/dev-secret-key-change-in-production/$secret_key/" .env
    echo "🔑 Generated secure secret key"
fi

# Create RemoveBG plugin
echo "🔌 Creating RemoveBG plugin..."
mkdir -p plugins/installed/removebg
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

import requests
import base64
from io import BytesIO
from PIL import Image
import os

def execute(context):
    """
    Execute the Remove Background plugin
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
        if image_data.startswith('http'):
            response = requests.get(image_data)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to download image: {response.status_code}"
                }
            image_bytes = response.content
        else:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        
        result = remove_background(image_bytes, api_key)
        
        if result.get('success'):
            return {
                "success": True,
                "image": result['image'],
                "format": result['format'],
                "width": result['width'],
                "height": result['height'],
                "credits_charged": result['credits_charged'],
                "message": "Background removed successfully!"
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error')
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Processing failed: {str(e)}"
        }

def remove_background(image_bytes, api_key):
    try:
        url = "https://api.remove.bg/v1.0/removebg"
        headers = {'X-Api-Key': api_key}
        
        files = {
            'image_file': ('image.png', image_bytes),
            'size': (None, 'auto'),
            'type': (None, 'auto'),
        }
        
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            result_bytes = response.content
            img_base64 = base64.b64encode(result_bytes).decode('utf-8')
            img = Image.open(BytesIO(result_bytes))
            
            credits_charged = response.headers.get('X-Credits-Charged', 'Unknown')
            
            return {
                "success": True,
                "image": f"data:image/png;base64,{img_base64}",
                "format": img.format,
                "width": img.width,
                "height": img.height,
                "credits_charged": credits_charged
            }
        else:
            error_msg = f"API Error: {response.status_code}"
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    error_msg = error_data['errors'][0]['title']
            except:
                pass
            
            return {
                "success": False,
                "error": error_msg
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }
EOF

# Create __init__.py files
touch plugins/installed/__init__.py
touch plugins/__init__.py
touch core/__init__.py
touch core/plugin_system/__init__.py
touch core/security/__init__.py
touch core/utils/__init__.py
touch core/models/__init__.py

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run: python app.py"
echo "3. Open: http://localhost:5000"
echo ""
echo "🔑 Default Admin login (change after first login):"
echo "   Email: admin@abdullahhub.com"
echo "   Password: admin123"
echo ""
echo "📧 Configure email in .env file:"
echo "   MAIL_USERNAME=your-email@gmail.com"
echo "   MAIL_PASSWORD=hevl qfar pmjj siws"
echo ""
echo "🔑 Add your Remove.bg API key:"
echo "   REMOVEBG_API_KEY=xv5aoeuirxTNZBYS5KykZZEK"
