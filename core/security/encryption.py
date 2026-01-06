import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import secrets

def generate_key(password=None, salt=None):
    """Generate encryption key from password or generate random key"""
    if password:
        if not salt:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    else:
        return Fernet.generate_key(), None

def get_fernet():
    """Get Fernet instance with app secret key"""
    from flask import current_app
    
    secret_key = current_app.config['SECRET_KEY'].encode()
    key = base64.urlsafe_b64encode(secret_key.ljust(32)[:32])
    return Fernet(key)

def encrypt(data):
    """Encrypt data"""
    if not data:
        return None
    
    fernet = get_fernet()
    encrypted = fernet.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt(encrypted_data):
    """Decrypt data"""
    if not encrypted_data:
        return None
    
    try:
        fernet = get_fernet()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except:
        return None

def hash_api_key(api_key):
    """Create a secure hash of API key for verification"""
    import hashlib
    import hmac
    
    secret = os.environ.get('API_KEY_HASH_SECRET', 'default-secret-change-me')
    return hmac.new(
        secret.encode(),
        api_key.encode(),
        hashlib.sha256
    ).hexdigest()

def generate_api_key(length=32):
    """Generate a secure random API key"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_api_secret(length=64):
    """Generate a secure random API secret"""
    import secrets
    return secrets.token_urlsafe(length)

def mask_api_key(api_key, visible_chars=4):
    """Mask API key for display (show only last few characters)"""
    if not api_key or len(api_key) <= visible_chars:
        return '*' * 8
    
    return '*' * (len(api_key) - visible_chars) + api_key[-visible_chars:]
