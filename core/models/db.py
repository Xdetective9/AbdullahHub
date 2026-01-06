from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return db

# Import all models for SQLAlchemy to recognize them
from .user import User
from .plugin import Plugin, PluginInstallation
from .api_key import APIKey
