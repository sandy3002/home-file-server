import os

# Project root directory (one level up from app/)
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 10737418240))  # Default 10GB
    MONGODB_URI = os.environ.get('MONGODB_URI')

    # Resolve UPLOAD_FOLDER: expand ~, then make relative paths relative to project root
    _raw_folder = os.path.expanduser(os.environ.get('UPLOAD_FOLDER', '~/Documents/FileServer'))
    UPLOAD_FOLDER = _raw_folder if os.path.isabs(_raw_folder) else os.path.join(basedir, _raw_folder)
    
    # Security configurations
    if os.environ.get('FLASK_ENV') == 'production':
        SESSION_COOKIE_SECURE = True
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = 'Lax'
