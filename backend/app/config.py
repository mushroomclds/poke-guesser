import os
from dotenv import load_dotenv
from .utils.logger import logger

# Only load .env file locally (not in Azure)
if os.getenv("FLASK_ENV") == "development":
    logger.info("Loading environment variables from .env file")
    load_dotenv()

class Config:
    # Security - these should be class variables, not instance variables
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    # JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret')
    
    # Database
    ORACLE_USER = os.getenv('ORACLE_USER')
    ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD')
    ORACLE_DSN = os.getenv('ORACLE_DSN')

    # API
    POKEMON_API_KEY = os.getenv('POKEMON_API_KEY')
    
    # Application
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    TESTING = False
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5000').split(',')


# class DevelopmentConfig(Config):
#     DEBUG = True
#     CORS_ORIGINS = ['http://localhost:5000']

# class ProductionConfig(Config):
#     DEBUG = False
#     CORS_ORIGINS = ['https://']
