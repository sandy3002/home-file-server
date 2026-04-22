import os
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from ..security import login_required
from ..utils import allowed_file, get_file_info

files_bp = Blueprint('files', __name__)

@files_bp.route('/browse')
@files_bp.route('/browse/<path:subpath>')
@login_required
def browse_files(subpath=''):
    """Browse files in the server directory"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    current_path = os.path.join(upload_folder, subpath)
    
    # Security check - ensure we're not going outside upload folder
    if not os.path.abspath(current_path).startswith(os.path.abspath(upload_folder)):
        return redirect(url_for('files.browse_files'))
    
    if not os.path.exists(current_path):
        return redirect(url_for('files.browse_files'))
    
    items = []
    if os.path.isdir(current_path):
        # Add parent directory link if not in root
        if subpath:
            parent_path = str(Path(subpath).parent) if str(Path(subpath).parent) != '.' else ''
            # Normalize parent path to use forward slashes for web
            parent_path = parent_path.replace(os.sep, '/')
            items.append({
                'name': '..',
                'path': parent_path,
                'is_dir': True,
                'is_parent': True
            })
        
        # List directory contents using os.scandir for better performance
        try:
            with os.scandir(current_path) as entries:
                sorted_entries = sorted(entries, key=lambda e: e.name)
                for entry in sorted_entries:
                    if entry.name.startswith('.'):  # Skip hidden files
                        continue
                    
                    # Use forward slashes for web paths
                    relative_path = '/'.join(os.path.normpath(os.path.join(subpath, entry.name) if subpath else entry.name).split(os.sep))
                    
                    if entry.is_dir():
                        items.append({
                            'name': entry.name,
                            'path': relative_path,
                            'is_dir': True
                        })
                    else:
                        file_info = get_file_info(entry.path, is_dir_entry=True, entry=entry)
                        items.append({
                            'name': entry.name,
                            'path': relative_path,
                            'is_dir': False,
                            'info': file_info
                        })
        except OSError as e:
            print(f"Error scanning directory: {e}")
            pass
    
    return render_template('browse.html', items=items, current_path=subpath)

@files_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Handle file uploads"""
    if request.method == 'POST':
        upload_folder = current_app.config['UPLOAD_FOLDER']
        uploaded_files = request.files.getlist('files[]')
        upload_path = request.form.get('upload_path', '')
        
        target_dir = os.path.join(upload_folder, upload_path)
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

@files_bp.route('/download/<path:filepath>')
@login_required
def download_file(filepath):
    """Download a file"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = filepath.replace('/', os.sep)
    file_path = os.path.join(upload_folder, filepath)
    
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        return "Access denied", 403
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

@files_bp.route('/api/delete/<path:filepath>', methods=['POST'])
@login_required
def delete_file(filepath):
    """Delete a file or directory"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = filepath.replace('/', os.sep)
    file_path = os.path.join(upload_folder, filepath)
    
    if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            os.rmdir(file_path)  # Only removes empty directories
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@files_bp.route('/api/create_folder', methods=['POST'])
@login_required
def create_folder():
    """Create a new folder"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    data = request.get_json()
    folder_name = secure_filename(data.get('name', ''))
    current_path = data.get('path', '')
    
    if not folder_name:
        return jsonify({'success': False, 'error': 'Invalid folder name'}), 400
    
    folder_path = os.path.join(upload_folder, current_path, folder_name)
    
    try:
        os.makedirs(folder_path, exist_ok=False)
        return jsonify({'success': True})
    except FileExistsError:
        return jsonify({'success': False, 'error': 'Folder already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
