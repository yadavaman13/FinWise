#!/usr/bin/env python3
"""
FinSight Vercel Entry Point

This file serves as the entry point for Vercel deployment.
Vercel expects the Flask app to be available as 'app' from this file.
"""

from app import app, init_db
import os

# Initialize database on startup
init_db()

# Vercel expects the Flask app to be named 'app'
if __name__ == "__main__":
    # This won't run on Vercel, but useful for local testing
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)