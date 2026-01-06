from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import uuid
from app import db, app

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    avatar = db.Column(db.String(200))
    
    # Relationships
    plugins = db.relationship('PluginInstallation', backref='user', lazy=True, cascade='all, delete-orphan')
    api_keys = db.relationship('APIKey', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_auth_token(self, expires_in=86400):
        """Generate JWT token for API authentication"""
        return jwt.encode(
            {
                'user_id': self.id,
                'exp': datetime.utcnow() + timedelta(seconds=expires_in)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_auth_token(token):
        """Verify JWT token"""
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            return User.query.get(data['user_id'])
        except:
            return None
    
    def generate_verification_token(self, expires_in=3600):
        """Generate email verification token"""
        return jwt.encode(
            {
                'user_id': self.id,
                'purpose': 'verify_email',
                'exp': datetime.utcnow() + timedelta(seconds=expires_in)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    def generate_reset_token(self, expires_in=3600):
        """Generate password reset token"""
        return jwt.encode(
            {
                'user_id': self.id,
                'purpose': 'reset_password',
                'exp': datetime.utcnow() + timedelta(seconds=expires_in)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_token(token, purpose=None):
        """Verify token with optional purpose check"""
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            
            if purpose and data.get('purpose') != purpose:
                return None
            
            user = User.query.get(data['user_id'])
            return user if user and user.is_active else None
        except:
            return None
    
    def get_stats(self):
        """Get user statistics"""
        from .plugin import PluginInstallation
        from .api_key import APIKey
        
        return {
            'plugins_installed': PluginInstallation.query.filter_by(user_id=self.id).count(),
            'api_keys': APIKey.query.filter_by(user_id=self.id).count(),
            'account_age': (datetime.utcnow() - self.created_at).days
        }
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_verified': self.is_verified,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'avatar': self.avatar
        }
