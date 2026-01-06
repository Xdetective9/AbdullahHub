from datetime import datetime
import json
from app import db

class Plugin(db.Model):
    __tablename__ = 'plugins'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    version = db.Column(db.String(20), default='1.0.0')
    author = db.Column(db.String(100))
    category = db.Column(db.String(50))
    tags = db.Column(db.String(500))  # Comma separated tags
    
    # File information
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    file_hash = db.Column(db.String(64))
    
    # Requirements
    requirements = db.Column(db.Text)  # JSON string of requirements
    dependencies = db.Column(db.Text)  # JSON string of dependencies
    api_keys_required = db.Column(db.Text)  # JSON string of required API keys
    
    # Configuration
    config_schema = db.Column(db.Text)  # JSON schema for plugin configuration
    default_config = db.Column(db.Text)  # JSON default configuration
    
    # Status flags
    is_public = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)
    
    # Statistics
    download_count = db.Column(db.Integer, default=0)
    execution_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    published_at = db.Column(db.DateTime)
    
    # Relationships
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    installations = db.relationship('PluginInstallation', backref='plugin', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Plugin, self).__init__(**kwargs)
        if not self.tags:
            self.tags = self.category or 'general'
    
    def increment_download(self):
        """Increment download count"""
        self.download_count += 1
        db.session.commit()
    
    def increment_execution(self):
        """Increment execution count"""
        self.execution_count += 1
        db.session.commit()
    
    def update_rating(self, new_rating):
        """Update plugin rating"""
        total_rating = self.rating * self.review_count
        self.review_count += 1
        self.rating = (total_rating + new_rating) / self.review_count
        db.session.commit()
    
    def get_requirements(self):
        """Get requirements as list"""
        try:
            return json.loads(self.requirements) if self.requirements else []
        except:
            return []
    
    def get_dependencies(self):
        """Get dependencies as list"""
        try:
            return json.loads(self.dependencies) if self.dependencies else []
        except:
            return []
    
    def get_api_keys_required(self):
        """Get required API keys as list"""
        try:
            return json.loads(self.api_keys_required) if self.api_keys_required else []
        except:
            return []
    
    def get_config_schema(self):
        """Get configuration schema"""
        try:
            return json.loads(self.config_schema) if self.config_schema else {}
        except:
            return {}
    
    def get_default_config(self):
        """Get default configuration"""
        try:
            return json.loads(self.default_config) if self.default_config else {}
        except:
            return {}
    
    def to_dict(self, include_details=False):
        """Convert plugin to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else [],
            'is_premium': self.is_premium,
            'is_active': self.is_active,
            'download_count': self.download_count,
            'rating': self.rating,
            'review_count': self.review_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_details:
            data.update({
                'requirements': self.get_requirements(),
                'dependencies': self.get_dependencies(),
                'api_keys_required': self.get_api_keys_required(),
                'file_size': self.file_size,
                'execution_count': self.execution_count
            })
        
        return data

class PluginInstallation(db.Model):
    __tablename__ = 'plugin_installations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plugin_id = db.Column(db.Integer, db.ForeignKey('plugins.id'), nullable=False)
    
    # Installation settings
    config = db.Column(db.Text)  # JSON configuration
    is_active = db.Column(db.Boolean, default=True)
    is_enabled = db.Column(db.Boolean, default=True)
    
    # Statistics
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    
    # Timestamps
    installed_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'plugin_id', name='unique_user_plugin'),
    )
    
    def get_config(self):
        """Get installation configuration"""
        try:
            return json.loads(self.config) if self.config else {}
        except:
            return {}
    
    def update_config(self, new_config):
        """Update installation configuration"""
        current_config = self.get_config()
        current_config.update(new_config)
        self.config = json.dumps(current_config)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def increment_usage(self):
        """Increment usage count and update last used"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        db.session.commit()
