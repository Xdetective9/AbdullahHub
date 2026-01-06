#!/bin/bash
echo "🚀 Building AbdullahHub..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p storage/databases
mkdir -p storage/uploads
mkdir -p storage/logs
mkdir -p plugins/installed
mkdir -p plugins/temp
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
    print('✅ Database initialized')
"

echo "✅ Build completed successfully!"
