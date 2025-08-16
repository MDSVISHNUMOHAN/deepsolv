#!/usr/bin/env python3
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
