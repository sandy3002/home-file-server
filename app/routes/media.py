import os
import mimetypes
# pyrefly: ignore [missing-import]
from flask import Blueprint, render_template, request, send_file, Response, current_app
from ..security import login_required
from ..utils import get_file_info, MIME_TYPE_OVERRIDES

media_bp = Blueprint('media', __name__)

@media_bp.route('/stream/<path:filepath>')
@login_required
def stream_media(filepath):
    """Stream video or audio files"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = filepath.replace('/', os.sep)
    file_path = os.path.join(upload_folder, filepath)
    
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        return "Access denied", 403
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    file_info = get_file_info(file_path)
    
    # We replace os.sep with '/' for the frontend templating
    web_filepath = filepath.replace(os.sep, '/')
    
    if file_info['is_video']:
        return render_template('video_player.html', filepath=web_filepath, filename=os.path.basename(filepath))
    elif file_info['is_audio']:
        return render_template('audio_player.html', filepath=web_filepath, filename=os.path.basename(filepath))
    else:
        return "File is not streamable", 400

@media_bp.route('/media/<path:filepath>')
@login_required
def serve_media(filepath):
    """Serve media files with range support for streaming"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = filepath.replace('/', os.sep)
    file_path = os.path.join(upload_folder, filepath)
    
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        return "Access denied", 403
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    file_size = os.path.getsize(file_path)
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext in MIME_TYPE_OVERRIDES:
        mime_type = MIME_TYPE_OVERRIDES[file_ext]
    else:
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
    
    range_header = request.headers.get('Range', None)
    if range_header:
        byte_start = 0
        byte_end = file_size - 1
        
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
