#!/usr/bin/env python3
"""
Home File Server Dashboard
A web-based file server with upload, download, and streaming capabilities
"""

import os
import mimetypes
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, Response, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import zipfile
import tempfile
from urllib.parse import quote
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 10737418240))  # Default 10GB
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Security configurations
if os.environ.get('FLASK_ENV') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# MongoDB Configuration
MONGODB_URI = os.environ.get('MONGODB_URI')
try:
    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = mongo_client['home-file-server']
    users_collection = db['users']
    # Create unique index on username
    users_collection.create_index('username', unique=True)
    print("✓ Connected to MongoDB successfully")
except Exception as e:
    print(f"✗ MongoDB connection error: {e}")
    db = None
    users_collection = None

# Configuration
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.expanduser('~/Documents/FileServer'))
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mkv', 'webm', 'mov', 'wmv', 'flv', 'mp3', 'wav', 'flac', 'ogg', 'aac', 'm4a'])

# Video and audio format mappings for better MIME type support
MIME_TYPE_OVERRIDES = {
    '.mkv': 'video/x-matroska',
    '.webm': 'video/webm',
    '.mov': 'video/quicktime',
    '.wmv': 'video/x-ms-wmv',
    '.flv': 'video/x-flv',
    '.ogg': 'audio/ogg',
    '.aac': 'audio/aac',
    '.m4a': 'audio/mp4',
    '.pdf': 'application/pdf'
}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_file_info(filepath):
    """Get file information including size and type"""
    stat = os.stat(filepath)
    file_size = stat.st_size
    
    # Get file extension and check for MIME type override
    file_ext = os.path.splitext(filepath)[1].lower()
    if file_ext in MIME_TYPE_OVERRIDES:
        file_type = MIME_TYPE_OVERRIDES[file_ext]
    else:
        file_type = mimetypes.guess_type(filepath)[0] or 'unknown'
    
    # Human readable file size
    def format_bytes(bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"
    
    return {
        'size': format_bytes(file_size),
        'type': file_type,
        'is_video': file_type and (file_type.startswith('video/') or file_ext in ['.mkv', '.webm', '.mov', '.wmv', '.flv']),
        'is_audio': file_type and (file_type.startswith('audio/') or file_ext in ['.ogg', '.aac', '.m4a']),
        'is_image': file_type and file_type.startswith('image/'),
        'is_pdf': file_ext == '.pdf',
        'extension': file_ext
    }

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        if users_collection is None:
            flash('Database connection error', 'error')
            return render_template('login.html')
        
        user = users_collection.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if users_collection is None:
            flash('Database connection error', 'error')
            return render_template('register.html')
        
        # Check if username already exists
        if users_collection.find_one({'username': username}):
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        user_data = {
            'username': username,
            'password': hashed_password,
            'created_at': datetime.utcnow(),
            'last_login': None
        }
        
        try:
            result = users_collection.insert_one(user_data)
            session['user_id'] = str(result.inserted_id)
            session['username'] = username
            flash(f'Account created successfully! Welcome, {username}!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('index.html', username=session.get('username'))

@app.route('/browse')
@app.route('/browse/<path:subpath>')
@login_required
def browse_files(subpath=''):
    """Browse files in the server directory"""
    current_path = os.path.join(UPLOAD_FOLDER, subpath)
    
    # Security check - ensure we're not going outside upload folder
    if not os.path.abspath(current_path).startswith(os.path.abspath(UPLOAD_FOLDER)):
        return redirect(url_for('browse_files'))
    
    if not os.path.exists(current_path):
        return redirect(url_for('browse_files'))
    
    items = []
    if os.path.isdir(current_path):
        # Add parent directory link if not in root
        if subpath:
            parent_path = str(Path(subpath).parent) if str(Path(subpath).parent) != '.' else ''
            items.append({
                'name': '..',
                'path': parent_path,
                'is_dir': True,
                'is_parent': True
            })
        
        # List directory contents
        for item in sorted(os.listdir(current_path)):
            if item.startswith('.'):  # Skip hidden files
                continue
            
            item_path = os.path.join(current_path, item)
            relative_path = os.path.join(subpath, item) if subpath else item
            
            if os.path.isdir(item_path):
                items.append({
                    'name': item,
                    'path': relative_path,
                    'is_dir': True
                })
            else:
                file_info = get_file_info(item_path)
                items.append({
                    'name': item,
                    'path': relative_path,
                    'is_dir': False,
                    'info': file_info
                })
    
    return render_template('browse.html', items=items, current_path=subpath)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Handle file uploads"""
    if request.method == 'POST':
        uploaded_files = request.files.getlist('files[]')
        upload_path = request.form.get('upload_path', '')
        
        target_dir = os.path.join(UPLOAD_FOLDER, upload_path)
        os.makedirs(target_dir, exist_ok=True)
        
        results = []
        for file in uploaded_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                if allowed_file(filename):
                    filepath = os.path.join(target_dir, filename)
                    file.save(filepath)
                    results.append({'success': True, 'filename': filename})
                else:
                    results.append({'success': False, 'filename': filename, 'error': 'File type not allowed'})
        
        return jsonify({'results': results})
    
    return render_template('upload.html')

@app.route('/download/<path:filepath>')
@login_required
def download_file(filepath):
    """Download a file"""
    file_path = os.path.join(UPLOAD_FOLDER, filepath)
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_FOLDER)):
        return "Access denied", 403
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

@app.route('/stream/<path:filepath>')
@login_required
def stream_media(filepath):
    """Stream video or audio files"""
    file_path = os.path.join(UPLOAD_FOLDER, filepath)
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_FOLDER)):
        return "Access denied", 403
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    file_info = get_file_info(file_path)
    
    if file_info['is_video']:
        return render_template('video_player.html', filepath=filepath, filename=os.path.basename(filepath))
    elif file_info['is_audio']:
        return render_template('audio_player.html', filepath=filepath, filename=os.path.basename(filepath))
    else:
        return "File is not streamable", 400

@app.route('/media/<path:filepath>')
@login_required
def serve_media(filepath):
    """Serve media files with range support for streaming"""
    file_path = os.path.join(UPLOAD_FOLDER, filepath)
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_FOLDER)):
        return "Access denied", 403
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    # Get file info
    file_size = os.path.getsize(file_path)
    mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
    
    # Handle range requests for video streaming
    range_header = request.headers.get('Range', None)
    if range_header:
        byte_start = 0
        byte_end = file_size - 1
        
        if range_header:
            match = range_header.replace('bytes=', '').split('-')
            if match[0]:
                byte_start = int(match[0])
            if match[1]:
                byte_end = int(match[1])
        
        content_length = byte_end - byte_start + 1
        
        def generate():
            with open(file_path, 'rb') as f:
                f.seek(byte_start)
                remaining = content_length
                while remaining:
                    chunk_size = min(8192, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
        
        response = Response(generate(), 
                          206,
                          headers={
                              'Content-Type': mime_type,
                              'Accept-Ranges': 'bytes',
                              'Content-Range': f'bytes {byte_start}-{byte_end}/{file_size}',
                              'Content-Length': str(content_length)
                          })
        return response
    else:
        return send_file(file_path, mimetype=mime_type)

@app.route('/api/delete/<path:filepath>', methods=['POST'])
def delete_file(filepath):
    """Delete a file or directory"""
    file_path = os.path.join(UPLOAD_FOLDER, filepath)
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_FOLDER)):
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            os.rmdir(file_path)  # Only removes empty directories
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/create_folder', methods=['POST'])
def create_folder():
    """Create a new folder"""
    data = request.get_json()
    folder_name = secure_filename(data.get('name', ''))
    current_path = data.get('path', '')
    
    if not folder_name:
        return jsonify({'success': False, 'error': 'Invalid folder name'}), 400
    
    folder_path = os.path.join(UPLOAD_FOLDER, current_path, folder_name)
    
    try:
        os.makedirs(folder_path, exist_ok=False)
        return jsonify({'success': True})
    except FileExistsError:
        return jsonify({'success': False, 'error': 'Folder already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mpv/command/<path:filepath>')
def get_mpv_command(filepath):
    """Generate mpv command for a media file"""
    file_path = os.path.join(UPLOAD_FOLDER, filepath)
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_FOLDER)):
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    # Get server URL from request
    server_url = f"{request.scheme}://{request.host}"
    media_url = f"{server_url}/media/{filepath}"
    
    # Generate different mpv command variations
    file_ext = os.path.splitext(filepath)[1].lower()
    
    # Base commands
    commands = {
        'basic': f'mpv "{media_url}"',
        'cached': f'mpv --cache=yes --cache-secs=10 --hwdec=auto "{media_url}"',
        'high_quality': f'mpv --cache=yes --cache-secs=30 --profile=gpu-hq --scale=ewa_lanczossharp --cscale=ewa_lanczossharp "{media_url}"',
        'fullscreen': f'mpv --fs "{media_url}"',
        'loop': f'mpv --loop "{media_url}"'
    }
    
    # Add format-specific optimizations
    if file_ext == '.mkv':
        commands['mkv_optimized'] = f'mpv --cache=yes --cache-secs=20 --hwdec=auto --vo=gpu --audio-channels=7.1 --sub-auto=fuzzy "{media_url}"'
        commands['mkv_subtitles'] = f'mpv --cache=yes --hwdec=auto --sub-auto=all --sub-file-paths=. "{media_url}"'
    elif file_ext in ['.mp4', '.avi']:
        commands['optimized'] = f'mpv --cache=yes --cache-secs=15 --hwdec=vaapi --profile=fast "{media_url}"'
    elif file_ext in ['.webm']:
        commands['webm_optimized'] = f'mpv --cache=yes --hwdec=auto --vo=gpu --profile=gpu-hq "{media_url}"'
    elif file_ext in ['.flac', '.wav']:
        commands['audio_hq'] = f'mpv --no-video --audio-device=auto --volume=100 "{media_url}"'
    
    file_info = get_file_info(file_path)
    
    return jsonify({
        'success': True,
        'filename': os.path.basename(filepath),
        'url': media_url,
        'commands': commands,
        'file_info': file_info
    })

@app.route('/mpv/<path:filepath>')
def mpv_launch(filepath):
    """Generate an mpv playlist file for download"""
    file_path = os.path.join(UPLOAD_FOLDER, filepath)
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_FOLDER)):
        return "Access denied", 403
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    # Generate server URL
    server_url = f"{request.scheme}://{request.host}"
    media_url = f"{server_url}/media/{filepath}"
    
    # Create playlist content
    playlist_content = f"""# Home File Server - mpv Playlist
# Generated on {os.path.basename(filepath)}
{media_url}
"""
    
    # Return as downloadable playlist file
    response = Response(
        playlist_content,
        mimetype='application/x-mpegurl',
        headers={
            'Content-Disposition': f'attachment; filename="{os.path.basename(filepath)}.m3u"'
        }
    )
    
    return response

if __name__ == '__main__':
    # Get configuration from environment
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 8080))
    flask_env = os.environ.get('FLASK_ENV', 'development')
    debug_mode = flask_env != 'production'
    
    print(f"Starting Home File Server...")
    print(f"Environment: {flask_env}")
    print(f"Files will be stored in: {UPLOAD_FOLDER}")
    print(f"Listening on: {host}:{port}")
    if not debug_mode:
        print("⚠️  Running in production mode - debug is disabled")
        print("⚠️  Make sure SECRET_KEY is set to a secure value!")
    
    app.run(host=host, port=port, debug=debug_mode)