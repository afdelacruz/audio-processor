import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-key-please-change')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/audio_processor')
    
    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg', 'aac', 'm4a'}


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    MONGO_URI = os.environ.get('TEST_MONGO_URI', 'mongodb://localhost:27017/audio_processor_test')
    UPLOAD_FOLDER = 'test_uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # In production, these must be set in environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    MONGO_URI = os.environ.get('MONGO_URI')
    
    # Use a more secure upload folder in production
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/var/www/audio_processor/uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)