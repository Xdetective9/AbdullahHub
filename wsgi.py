"""
WSGI entry point for production servers
Used by Gunicorn, uWSGI, etc.
"""

import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app as application

if __name__ == '__main__':
    application.run()
