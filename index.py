import sys
import os

# Add the backend directory to sys.path so all modules resolve correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# Vercel calls this 'app' as the WSGI entrypoint
app = create_app()

# Vercel handler
handler = app
