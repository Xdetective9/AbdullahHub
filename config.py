import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Basic
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///storage/databases/abdullahhub.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # File Upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    UPLOAD_FOLDER = 'storage/uploads'
    ALLOWED_EXTENSIONS = {'py', 'js', 'json', 'zip', 'tar.gz'}
    
    # Email (Google SMTP with your provided password)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'hevl qfar pmjj siws')  # Your app password
    MAIL_DEFAULT_SENDER = ('AbdullahHub Support', 'support@abdullahhub.com')
    
    # Plugin System
    PLUGINS_DIR = 'plugins/installed'
    TEMP_DIR = 'plugins/temp'
    SANDBOX_TIMEOUT = 30  # seconds
    
    # API
    API_RATE_LIMIT = "100/hour"
    
    # RemoveBG API (Your provided API key)
    REMOVEBG_API_KEY = os.environ.get('REMOVEBG_API_KEY', 'xv5aoeuirxTNZBYS5KykZZEK')
    
    # Admin
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@abdullahhub.com')
    
    # Stripe (for payments if needed)
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    # Analytics
    GOOGLE_ANALYTICS_ID = os.environ.get('GA_ID', '')
    
    # Feature Flags
    ENABLE_PAYMENTS = os.environ.get('ENABLE_PAYMENTS', 'false').lower() == 'true'
    ENABLE_EMAIL_VERIFICATION = os.environ.get('ENABLE_EMAIL_VERIFICATION', 'true').lower() == 'true'
    AUTO_APPROVE_PLUGINS = os.environ.get('AUTO_APPROVE_PLUGINS', 'false').lower() == 'true'
