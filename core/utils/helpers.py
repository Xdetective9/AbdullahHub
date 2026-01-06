import os
import json
import re
import uuid
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import secrets
import string

def generate_api_key(length=32):
    """Generate secure API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secure_filename(filename):
    """Generate secure filename"""
    name, ext = os.path.splitext(filename)
    name = re.sub(r'[^\w\-]', '_', name)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_str = secrets.token_hex(4)
    return f"{name}_{timestamp}_{random_str}{ext}"

def validate_email(email):
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, "Password is valid"

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_file_hash(file_path):
    """Calculate SHA256 hash of file"""
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def create_directory_structure(base_path, structure):
    """Create directory structure"""
    for name, contents in structure.items():
        path = os.path.join(base_path, name)
        
        if isinstance(contents, dict):
            os.makedirs(path, exist_ok=True)
            create_directory_structure(path, contents)
        else:
            os.makedirs(path, exist_ok=True)

def json_response(data=None, message="", status="success", code=200):
    """Create standardized JSON response"""
    response = {
        "status": status,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response), code

def paginate_query(query, page=1, per_page=20):
    """Paginate SQLAlchemy query"""
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        "items": [item.to_dict() for item in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }

def rate_limit(max_requests=100, window=3600):
    """Decorator for rate limiting"""
    from collections import defaultdict
    import time
    
    requests = defaultdict(list)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.remote_addr
            
            # Clean old requests
            current_time = time.time()
            requests[client_ip] = [req_time for req_time in requests[client_ip] 
                                  if current_time - req_time < window]
            
            # Check rate limit
            if len(requests[client_ip]) >= max_requests:
                return json_response(
                    message="Rate limit exceeded",
                    status="error",
                    code=429
                )
            
            # Add current request
            requests[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal"""
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    return filename

def generate_otp(length=6):
    """Generate numeric OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def calculate_expiry_time(hours=24):
    """Calculate expiry time"""
    return datetime.utcnow() + timedelta(hours=hours)

def is_expired(expiry_time):
    """Check if expiry time has passed"""
    return datetime.utcnow() > expiry_time

def mask_string(string, visible=4):
    """Mask string for display (show only last few characters)"""
    if not string or len(string) <= visible:
        return '*' * 8
    
    return '*' * (len(string) - visible) + string[-visible:]

def parse_boolean(value):
    """Parse boolean from string"""
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ['true', 'yes', '1', 'on']
    
    return bool(value)

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr
