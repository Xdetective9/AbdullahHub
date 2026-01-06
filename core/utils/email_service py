import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template
from threading import Thread
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email service with Flask app"""
        self.app = app
        self.mail_server = app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        self.mail_port = app.config.get('MAIL_PORT', 587)
        self.mail_username = app.config.get('MAIL_USERNAME')
        self.mail_password = app.config.get('MAIL_PASSWORD')
        self.mail_use_tls = app.config.get('MAIL_USE_TLS', True)
        self.mail_default_sender = app.config.get('MAIL_DEFAULT_SENDER', 'noreply@abdullahhub.com')
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test email connection"""
        try:
            server = smtplib.SMTP(self.mail_server, self.mail_port)
            server.ehlo()
            if self.mail_use_tls:
                server.starttls()
            if self.mail_username and self.mail_password:
                server.login(self.mail_username, self.mail_password)
            server.quit()
            logger.info("Email connection test successful")
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email"""
        if not self.mail_username or not self.mail_password:
            logger.warning("Email credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.mail_default_sender
            msg['To'] = to_email
            
            # Attach HTML and text content
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send in background thread
            thread = Thread(target=self._send_email_thread, args=(msg, to_email))
            thread.daemon = True
            thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _send_email_thread(self, msg, to_email):
        """Send email in background thread"""
        with self.app.app_context():
            try:
                server = smtplib.SMTP(self.mail_server, self.mail_port)
                server.ehlo()
                if self.mail_use_tls:
                    server.starttls()
                server.login(self.mail_username, self.mail_password)
                server.send_message(msg)
                server.quit()
                logger.info(f"Email sent successfully to {to_email}")
            except Exception as e:
                logger.error(f"Failed to send email in thread: {e}")
    
    def send_verification_email(self, to_email, verification_token):
        """Send email verification email"""
        verification_url = f"{self.app.config.get('BASE_URL', 'http://localhost:5000')}/verify/{verification_token}"
        
        html_content = render_template('emails/verification.html',
                                     verification_url=verification_url)
        
        text_content = f"Please verify your email by clicking: {verification_url}"
        
        return self.send_email(
            to_email=to_email,
            subject="Verify Your AbdullahHub Account",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_password_reset_email(self, to_email, reset_token):
        """Send password reset email"""
        reset_url = f"{self.app.config.get('BASE_URL', 'http://localhost:5000')}/reset-password/{reset_token}"
        
        html_content = render_template('emails/password_reset.html',
                                     reset_url=reset_url)
        
        text_content = f"Reset your password: {reset_url}"
        
        return self.send_email(
            to_email=to_email,
            subject="Reset Your AbdullahHub Password",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_welcome_email(self, to_email, username):
        """Send welcome email"""
        html_content = render_template('emails/welcome.html',
                                     username=username)
        
        text_content = f"Welcome to AbdullahHub, {username}! Start exploring plugins."
        
        return self.send_email(
            to_email=to_email,
            subject="Welcome to AbdullahHub!",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_plugin_approved_email(self, to_email, plugin_name):
        """Send plugin approval email"""
        html_content = render_template('emails/plugin_approved.html',
                                     plugin_name=plugin_name)
        
        text_content = f"Your plugin '{plugin_name}' has been approved!"
        
        return self.send_email(
            to_email=to_email,
            subject=f"Plugin Approved: {plugin_name}",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_admin_notification(self, subject, message):
        """Send notification to admin"""
        admin_email = self.app.config.get('ADMIN_EMAIL')
        if not admin_email:
            return False
        
        html_content = f"<h3>Admin Notification</h3><p>{message}</p>"
        
        return self.send_email(
            to_email=admin_email,
            subject=f"[Admin] {subject}",
            html_content=html_content,
            text_content=message
        )
