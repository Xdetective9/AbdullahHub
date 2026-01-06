from setuptools import setup, find_packages

setup(
    name="abdullahhub",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask==2.3.3',
        'Flask-SQLAlchemy==3.0.5',
        'Flask-Login==0.6.2',
        'Flask-WTF==1.1.1',
        'Flask-CORS==4.0.0',
        'Flask-Limiter==3.3.3',
        'Flask-Mail==0.9.1',
        'Flask-Talisman==0.8.1',
        'SQLAlchemy==2.0.19',
        'bcrypt==4.0.1',
        'cryptography==41.0.5',
        'PyJWT==2.8.0',
        'python-dotenv==1.0.0',
        'Pillow==10.0.1',
        'requests==2.31.0',
        'gunicorn==20.1.0',
        'whitenoise==6.5.0',
        'psutil==5.9.6',
        'email-validator==2.0.0'
    ],
    entry_points={
        'console_scripts': [
            'abdullahhub=app:main',
        ],
    },
)
