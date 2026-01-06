from datetime import datetime
from app import db
from core.security.encryption import encrypt, decrypt

class APIKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plugin_id = db.Column(db.Integer, db.ForeignKey('plugins.id'), nullable=False)
    
    # API key details
    name = db.Column(db.String(100))
    api_key = db.Column(db.Text)  # Encrypted
    api_secret = db.Column(db.Text)  # Encrypted
    api_url = db.Column(db.String(500))
    
    # Configuration
    is_active = db.Column(db.Boolean, default=True)
    environment = db.Column(db.String(20), default='production')  # sandbox/production
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    rate_limit = db.Column(db.Integer, default=100)  # requests per hour
    
    # Security
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_api_key(self, api_key):
        """Encrypt and store API key"""
        self.api_key = encrypt(api_key)
    
    def get_api_key(self):
        """Decrypt and return API key"""
        return decrypt(self.api_key) if self.api_key else None
    
    def set_api_secret(self, api_secret):
        """Encrypt and store API secret"""
        self.api_secret = encrypt(api_secret)
    
    def get_api_secret(self):
        """Decrypt and return API secret"""
        return decrypt(self.api_secret) if self.api_secret else None
    
    def is_expired(self):
        """Check if API key is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_secrets=False):
        """Convert API key to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'plugin_id': self.plugin_id,
            'is_active': self.is_active,
            'environment': self.environment,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
        
        if include_secrets:
            data['api_key'] = self.get_api_key()
            data['api_secret'] = self.get_api_secret()
            data['api_url'] = self.api_url
        
        return data
