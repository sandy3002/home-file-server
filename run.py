import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8080))
    flask_env = os.environ.get('FLASK_ENV', 'development')
    debug_mode = flask_env != 'production'
    
    print(f"Starting Home File Server...")
    print(f"Environment: {flask_env}")
    print(f"Listening on: {host}:{port}")
    if not debug_mode:
        print("⚠️  Running in production mode - debug is disabled")
        print("⚠️  Make sure SECRET_KEY is set to a secure value!")
    
    app.run(host=host, port=port, debug=debug_mode)
