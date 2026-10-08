import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the backend
BASE_DIR = Path(__file__).resolve().parent

# Load .env file if it exists
load_dotenv(BASE_DIR / '.env')

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'medifind-dev-default-secret-key-2026')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    
    # SQLite database file inside backend directory
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'medifind.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS Origins
    FRONTEND_ORIGINS = [
        origin.strip() for origin in os.getenv(
            'FRONTEND_ORIGIN', 
            'http://127.0.0.1:5500,http://localhost:5500,http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:8080,http://localhost:8080'
        ).split(',') if origin.strip()
    ]
    
    # File upload settings
    UPLOAD_FOLDER = BASE_DIR / os.getenv('UPLOAD_FOLDER', 'uploads/prescriptions')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', str(5 * 1024 * 1024))) # 5MB limit
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


class TestingConfig(Config):
    """Testing configuration with in-memory or test SQLite database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = BASE_DIR / 'uploads' / 'test_prescriptions'
