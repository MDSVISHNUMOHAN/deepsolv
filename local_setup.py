#!/usr/bin/env python3
"""
Local Setup Script for Shopify Insights Extractor
Run this to set up the application for local Windows development
"""

import os
import sys
import subprocess

def install_dependencies():
    """Install required dependencies."""
    dependencies = [
        'Flask==3.1.1',
        'Flask-SQLAlchemy==3.1.1', 
        'Flask-Migrate==4.1.0',
        'requests==2.32.4',
        'beautifulsoup4==4.13.4',
        'lxml==5.4.0',
        'psycopg2-binary==2.9.10',
        'gunicorn==23.0.0',
        'trafilatura==2.0.0',
        'openai==1.99.9',
        'email-validator==2.2.0'
    ]
    
    print("Installing dependencies...")
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"✓ Installed {dep}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {dep}")
            
def setup_local_config():
    """Set up local configuration."""
    print("Setting up local configuration...")
    
    # Create .env file for local development
    env_content = """# Local Development Configuration
SESSION_SECRET=local_dev_secret_key_12345
DATABASE_URL=sqlite:///local_shopify_insights.db
FLASK_ENV=development
FLASK_DEBUG=1
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✓ Created .env file for local development")
    
def create_local_app():
    """Create local app runner."""
    local_app_content = """#!/usr/bin/env python3
# Local Application Runner for Windows
# Double-click this file or run: python local_app.py

import os
from app import app, db

# Load environment variables from .env file
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Override database for local development
if not os.environ.get('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'sqlite:///local_shopify_insights.db'

if __name__ == '__main__':
    print("🚀 Starting Shopify Insights Extractor...")
    print("📱 Open your browser to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Create tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database initialized")
        except Exception as e:
            print(f"Warning: Database setup issue: {e}")
    
    # Run the application
    app.run(
        host='127.0.0.1',  # Localhost for Windows
        port=5000,
        debug=True,
        use_reloader=True
    )
"""
    
    with open('local_app.py', 'w', encoding='utf-8') as f:
        f.write(local_app_content)
    print("✓ Created local_app.py runner")

def create_local_config():
    """Create local configuration file."""
    local_config_content = """# local_config.py
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
"""
    
    with open('local_config.py', 'w', encoding='utf-8') as f:
        f.write(local_config_content)
    print("✓ Created local_config.py")

def main():
    print("🔧 Shopify Insights Extractor - Local Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    install_dependencies()
    
    # Set up configuration
    setup_local_config()
    
    # Create local app runner
    create_local_app()
    
    # Create local config
    create_local_config()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Run: python local_app.py")
    print("2. Open browser to: http://localhost:5000")
    print("3. Start analyzing Shopify stores!")
    print("\n💡 Tips:")
    print("- Data is stored in local_shopify_insights.db")
    print("- Check .env file for configuration")
    print("- Use local_config.py to customize settings")

if __name__ == '__main__':
    main()
