from functools import wraps
from flask import request, jsonify, current_app
from flask_login import LoginManager, current_user
import jwt
from datetime import datetime

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from core.models.user import User
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    if request.accept_mimetypes.accept_json:
        return jsonify({'error': 'Authentication required'}), 401
    return login_manager.unauthorized()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Decode token
            from core.models.user import User
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def rate_limit_by_ip(f):
    """Rate limit by IP address"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
        
        return limiter.limit("10 per minute")(f)(*args, **kwargs)
    
    return decorated

def verify_recaptcha(f):
    """Verify Google reCAPTCHA"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_app.config.get('ENABLE_RECAPTCHA', False):
            recaptcha_response = request.form.get('g-recaptcha-response')
            
            if not recaptcha_response:
                return jsonify({'error': 'Please complete the reCAPTCHA'}), 400
            
            # Verify with Google
            import requests
            secret_key = current_app.config.get('RECAPTCHA_SECRET_KEY')
            
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': secret_key,
                    'response': recaptcha_response
                }
            )
            
            result = response.json()
            
            if not result.get('success'):
                return jsonify({'error': 'Invalid reCAPTCHA'}), 400
        
        return f(*args, **kwargs)
    
    return decorated
