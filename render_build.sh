#!/bin/bash
echo "🚀 Building AbdullahHub for Render..."

# Create directory structure
mkdir -p storage/databases storage/uploads storage/logs
mkdir -p plugins/installed plugins/temp

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database tables created')
"

echo "✅ Build completed!"
