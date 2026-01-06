import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from flask_talisman import Talisman
import json
import uuid

# Import custom modules
from core.models.db import db, init_db
from core.models.user import User, APIKey, Plugin, PluginInstallation
from core.security.auth import login_manager, admin_required, current_user
from core.plugin_system.plugin_loader import PluginLoader
from core.plugin_system.plugin_analyzer import PluginAnalyzer
from core.plugin_system.dependency_manager import DependencyManager
from core.utils.email_service import EmailService
from core.utils.helpers import generate_api_key, validate_email
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('storage/logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create app
app = Flask(__name__)
app.config.from_object(Config)

# Security headers
Talisman(app, content_security_policy={
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"],
    'style-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net"],
    'img-src': ["'self'", "data:", "https:"]
})

# Enable CORS
CORS(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
mail = Mail(app)

# Initialize services
email_service = EmailService(app)
plugin_loader = PluginLoader()
plugin_analyzer = PluginAnalyzer()
dependency_manager = DependencyManager()

# Ensure directories exist
Path("storage/uploads").mkdir(parents=True, exist_ok=True)
Path("storage/logs").mkdir(parents=True, exist_ok=True)
Path("plugins/installed").mkdir(parents=True, exist_ok=True)
Path("plugins/temp").mkdir(parents=True, exist_ok=True)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server error: {error}")
    return render_template('errors/500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "success": False,
        "error": "Rate limit exceeded. Please try again later."
    }), 429

# Home routes
@app.route('/')
def index():
    """Home page with stunning animations"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/features')
def features():
    """Features showcase page"""
    return render_template('features.html')

@app.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')

@app.route('/contact')
def contact():
    """Contact page with support form"""
    return render_template('contact.html')

# Auth routes
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_verified:
                flash('Please verify your email first!', 'warning')
                return render_template('auth/verify_email.html', email=email)
            
            login_user(user, remember=remember)
            logger.info(f"User logged in: {email}")
            
            # Generate JWT token for API access
            session['api_token'] = user.generate_auth_token()
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not validate_email(email):
            flash('Invalid email address', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
        else:
            # Create user
            user = User(
                username=username,
                email=email,
                is_verified=False,
                is_admin=False
            )
            user.set_password(password)
            
            # Generate verification token
            verification_token = user.generate_verification_token()
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            try:
                email_service.send_verification_email(email, verification_token)
                flash('Account created! Please check your email for verification.', 'success')
                return render_template('auth/verify_email.html', email=email)
            except Exception as e:
                logger.error(f"Email sending failed: {e}")
                flash('Account created but verification email failed. Contact support.', 'warning')
                return redirect(url_for('login'))
    
    return render_template('auth/signup.html')

@app.route('/verify/<token>')
def verify_email(token):
    user = User.verify_token(token)
    if user:
        user.is_verified = True
        db.session.commit()
        flash('Email verified successfully! You can now login.', 'success')
        return redirect(url_for('login'))
    else:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('signup'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            reset_token = user.generate_reset_token()
            try:
                email_service.send_password_reset_email(email, reset_token)
                flash('Password reset instructions sent to your email.', 'success')
            except Exception as e:
                logger.error(f"Password reset email failed: {e}")
                flash('Failed to send reset email. Please try again.', 'danger')
        else:
            flash('If an account exists, reset instructions will be sent.', 'info')
    
    return render_template('auth/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        user.set_password(password)
        db.session.commit()
        flash('Password reset successfully! You can now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/reset_password.html', token=token)

@app.route('/logout')
def logout():
    session.clear()
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('index'))

# Dashboard routes
@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with animated stats"""
    user_plugins = PluginInstallation.query.filter_by(user_id=current_user.id).all()
    installed_plugins = [install.plugin for install in user_plugins]
    
    # Get user stats
    stats = {
        'total_plugins': len(installed_plugins),
        'active_plugins': sum(1 for p in installed_plugins if p.is_active),
        'api_calls': APIKey.query.filter_by(user_id=current_user.id).count(),
        'storage_used': 0  # Would calculate from uploaded files
    }
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         plugins=installed_plugins,
                         recent_activity=[])

# Plugin marketplace
@app.route('/plugins/marketplace')
@login_required
def plugin_marketplace():
    """Plugin marketplace with search and filters"""
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Plugin.query.filter_by(is_public=True, is_approved=True)
    
    if search:
        query = query.filter(
            (Plugin.name.ilike(f'%{search}%')) |
            (Plugin.description.ilike(f'%{search}%'))
        )
    
    if category:
        query = query.filter_by(category=category)
    
    plugins = query.all()
    categories = db.session.query(Plugin.category).distinct().all()
    
    return render_template('plugins/marketplace.html', 
                         plugins=plugins,
                         categories=[c[0] for c in categories if c[0]])

@app.route('/plugins/<plugin_id>')
@login_required
def plugin_detail(plugin_id):
    """Plugin detail page"""
    plugin = Plugin.query.get_or_404(plugin_id)
    is_installed = PluginInstallation.query.filter_by(
        user_id=current_user.id, 
        plugin_id=plugin.id
    ).first() is not None
    
    return render_template('plugins/plugin_detail.html', 
                         plugin=plugin, 
                         is_installed=is_installed)

@app.route('/plugins/install/<plugin_id>', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def install_plugin(plugin_id):
    """Install plugin for user"""
    plugin = Plugin.query.get_or_404(plugin_id)
    
    # Check if already installed
    existing = PluginInstallation.query.filter_by(
        user_id=current_user.id,
        plugin_id=plugin.id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'Plugin already installed'})
    
    # Create installation record
    installation = PluginInstallation(
        user_id=current_user.id,
        plugin_id=plugin.id,
        installed_at=datetime.utcnow()
    )
    
    # Install dependencies
    try:
        dependency_manager.install_dependencies(plugin.requirements)
        
        db.session.add(installation)
        db.session.commit()
        
        # Load plugin into system
        plugin_loader.load_plugin(plugin)
        
        logger.info(f"Plugin installed: {plugin.name} for user {current_user.id}")
        return jsonify({
            'success': True,
            'message': f'Plugin {plugin.name} installed successfully!'
        })
    except Exception as e:
        logger.error(f"Plugin installation failed: {e}")
        return jsonify({
            'success': False,
            'message': f'Installation failed: {str(e)}'
        }), 500

@app.route('/plugins/uninstall/<plugin_id>', methods=['POST'])
@login_required
def uninstall_plugin(plugin_id):
    """Uninstall plugin"""
    installation = PluginInstallation.query.filter_by(
        user_id=current_user.id,
        plugin_id=plugin_id
    ).first_or_404()
    
    db.session.delete(installation)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Plugin uninstalled successfully!'
    })

@app.route('/plugins/execute/<plugin_id>', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def execute_plugin(plugin_id):
    """Execute a plugin"""
    plugin = Plugin.query.get_or_404(plugin_id)
    
    # Check if user has plugin installed
    installation = PluginInstallation.query.filter_by(
        user_id=current_user.id,
        plugin_id=plugin.id
    ).first()
    
    if not installation:
        return jsonify({
            'success': False,
            'error': 'Plugin not installed'
        }), 403
    
    # Get input data
    data = request.get_json() or {}
    files = request.files
    
    try:
        # Execute plugin
        result = plugin_loader.execute_plugin(
            plugin_id=plugin.id,
            user_id=current_user.id,
            input_data=data,
            files=files
        )
        
        logger.info(f"Plugin executed: {plugin.name} by user {current_user.id}")
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"Plugin execution failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API Management
@app.route('/api/keys', methods=['GET', 'POST'])
@login_required
def manage_api_keys():
    """Manage API keys for plugins"""
    if request.method == 'POST':
        plugin_id = request.form.get('plugin_id')
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        
        if not plugin_id:
            return jsonify({'success': False, 'error': 'Plugin ID required'}), 400
        
        # Create or update API key
        existing = APIKey.query.filter_by(
            user_id=current_user.id,
            plugin_id=plugin_id
        ).first()
        
        if existing:
            existing.api_key = api_key
            existing.api_secret = api_secret
            existing.updated_at = datetime.utcnow()
        else:
            new_key = APIKey(
                user_id=current_user.id,
                plugin_id=plugin_id,
                api_key=api_key,
                api_secret=api_secret
            )
            db.session.add(new_key)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'API key saved'})
    
    # GET request - list API keys
    api_keys = APIKey.query.filter_by(user_id=current_user.id).all()
    return render_template('api_keys.html', api_keys=api_keys)

# Admin routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with system stats"""
    total_users = User.query.count()
    total_plugins = Plugin.query.count()
    active_plugins = Plugin.query.filter_by(is_active=True).count()
    pending_plugins = Plugin.query.filter_by(is_approved=False).count()
    
    # System info
    import psutil
    system_info = {
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'uptime': os.popen('uptime -p').read().strip()
    }
    
    return render_template('admin/admin_dashboard.html',
                         total_users=total_users,
                         total_plugins=total_plugins,
                         active_plugins=active_plugins,
                         pending_plugins=pending_plugins,
                         system_info=system_info)

@app.route('/admin/plugins', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_plugin_manager():
    """Admin plugin management"""
    if request.method == 'POST':
        action = request.form.get('action')
        plugin_id = request.form.get('plugin_id')
        
        plugin = Plugin.query.get_or_404(plugin_id)
        
        if action == 'approve':
            plugin.is_approved = True
            plugin.approved_by = current_user.id
            plugin.approved_at = datetime.utcnow()
            flash(f'Plugin {plugin.name} approved!', 'success')
        
        elif action == 'reject':
            reason = request.form.get('reason', '')
            plugin.is_approved = False
            # Notify plugin owner
            flash(f'Plugin {plugin.name} rejected.', 'warning')
        
        elif action == 'toggle':
            plugin.is_active = not plugin.is_active
            status = 'activated' if plugin.is_active else 'deactivated'
            flash(f'Plugin {plugin.name} {status}!', 'info')
        
        elif action == 'delete':
            # Archive instead of delete
            plugin.is_archived = True
            flash(f'Plugin {plugin.name} archived!', 'danger')
        
        db.session.commit()
    
    plugins = Plugin.query.filter_by(is_archived=False).order_by(Plugin.created_at.desc()).all()
    return render_template('admin/plugin_manager.html', plugins=plugins)

@app.route('/admin/upload-plugin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_upload_plugin():
    """Admin upload and analyze plugin"""
    if request.method == 'POST':
        # Check if file uploaded
        if 'plugin_file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(request.url)
        
        file = request.files['plugin_file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        temp_path = os.path.join('plugins/temp', filename)
        file.save(temp_path)
        
        try:
            # Analyze plugin
            analysis = plugin_analyzer.analyze_plugin(temp_path)
            
            # Create plugin record
            plugin = Plugin(
                name=analysis['name'],
                description=analysis['description'],
                version=analysis['version'],
                author=analysis['author'],
                category=analysis['category'],
                requirements=json.dumps(analysis['requirements']),
                api_keys_required=json.dumps(analysis['api_keys_required']),
                file_path=temp_path,
                uploaded_by=current_user.id,
                is_approved=True,  # Auto-approve for admin
                is_active=True
            )
            
            db.session.add(plugin)
            db.session.commit()
            
            # Install dependencies
            dependency_manager.install_dependencies(analysis['requirements'])
            
            # Move to installed plugins
            install_path = f"plugins/installed/{plugin.id}_{filename}"
            os.rename(temp_path, install_path)
            plugin.file_path = install_path
            db.session.commit()
            
            flash(f'Plugin {plugin.name} uploaded and analyzed successfully!', 'success')
            return redirect(url_for('admin_plugin_manager'))
            
        except Exception as e:
            logger.error(f"Plugin upload failed: {e}")
            flash(f'Plugin analysis failed: {str(e)}', 'danger')
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    return render_template('admin/upload_plugin.html')

@app.route('/admin/users')
@login_required
@admin_required
def admin_user_manager():
    """Manage users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/user_manager.html', users=users)

@app.route('/admin/system')
@login_required
@admin_required
def admin_system_status():
    """System status and logs"""
    import subprocess
    
    # Get recent logs
    log_lines = []
    try:
        with open('storage/logs/app.log', 'r') as f:
            log_lines = f.readlines()[-100:]  # Last 100 lines
    except:
        pass
    
    # Get installed packages
    packages = []
    try:
        result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
        packages = result.stdout.split('\n')[2:]  # Skip header
    except:
        pass
    
    return render_template('admin/system_status.html', 
                         logs=log_lines,
                         packages=packages)

# API Routes
@app.route('/api/v1/plugins', methods=['GET'])
@limiter.limit("60 per minute")
def api_list_plugins():
    """Public API: List all public plugins"""
    plugins = Plugin.query.filter_by(is_public=True, is_active=True).all()
    
    result = []
    for plugin in plugins:
        result.append({
            'id': plugin.id,
            'name': plugin.name,
            'description': plugin.description,
            'version': plugin.version,
            'author': plugin.author,
            'category': plugin.category,
            'downloads': plugin.download_count,
            'rating': plugin.rating
        })
    
    return jsonify({'success': True, 'plugins': result})

@app.route('/api/v1/execute', methods=['POST'])
@limiter.limit("30 per minute")
def api_execute_plugin():
    """API endpoint for plugin execution"""
    api_key = request.headers.get('X-API-Key')
    plugin_id = request.json.get('plugin_id')
    
    if not api_key:
        return jsonify({'success': False, 'error': 'API key required'}), 401
    
    # Verify API key
    key_record = APIKey.query.filter_by(api_key=api_key).first()
    if not key_record:
        return jsonify({'success': False, 'error': 'Invalid API key'}), 401
    
    # Verify plugin access
    plugin = Plugin.query.get(plugin_id)
    if not plugin or not plugin.is_active:
        return jsonify({'success': False, 'error': 'Plugin not available'}), 404
    
    # Execute plugin
    try:
        result = plugin_loader.execute_plugin(
            plugin_id=plugin.id,
            user_id=key_record.user_id,
            input_data=request.json.get('data', {}),
            api_key=api_key
        )
        
        # Log API call
        key_record.last_used = datetime.utcnow()
        key_record.usage_count += 1
        db.session.commit()
        
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"API execution failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Webhook for payment notifications (if needed)
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Stripe webhook handler for payments"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, Config.STRIPE_WEBHOOK_SECRET
        )
        
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            # Handle successful payment
            logger.info(f"Payment succeeded: {payment_intent['id']}")
        
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'success': False}), 400

# Health check endpoint for deployment platforms
@app.route('/health')
def health_check():
    """Health check for deployment platforms"""
    try:
        # Check database
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Initialize database
@app.before_first_request
def initialize():
    """Initialize database and load plugins"""
    with app.app_context():
        init_db()
        plugin_loader.load_all_plugins()
        logger.info("Application initialized successfully")

if __name__ == '__main__':
    # Run with production settings
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    )
