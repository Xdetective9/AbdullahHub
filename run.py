#!/usr/bin/env python3
"""
AbdullahHub - Entry Point
Run with: python run.py
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # Check environment
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=debug,
        threaded=True
    )
