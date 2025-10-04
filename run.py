#!/usr/bin/env python3
"""
FinSight Startup Script

This script initializes and runs the FinSight Flask application.
"""

import os
import sys
from app import app, init_db

def setup_environment():
    """Setup the environment for the application"""
    # Create necessary directories
    directories = ['database', 'uploads', 'static/css', 'static/js', 'templates']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")

if __name__ == '__main__':
    print("=== FinSight ===")
    print("Setting up environment...")

    setup_environment()

    print("Starting server...")
    print("Access the application at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")

    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
