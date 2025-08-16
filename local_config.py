# local_config.py
# Local configuration overrides

import os

class LocalConfig:
    # Database configuration for local development
    SQLALCHEMY_DATABASE_URI = 'sqlite:///local_shopify_insights.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = 'local_dev_secret_key_12345'
    
    # Debug mode
    DEBUG = True
    TESTING = False
    
    # SQLAlchemy engine options
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
