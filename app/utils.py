import os
import mimetypes

# Expanded allowed extensions to include more documents, archives, code files, and media
ALLOWED_EXTENSIONS = set([
    # Documents
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'csv',
    # Images
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'bmp', 'svg', 'tif', 'tiff',
    # Video
    'mp4', 'avi', 'mkv', 'webm', 'mov', 'wmv', 'flv', 'ts', 'm4v',
    # Audio
    'mp3', 'wav', 'flac', 'ogg', 'aac', 'm4a', 'aiff', 'wma', 'opus',
    # Archives
    'zip', 'rar', '7z', 'tar', 'gz',
    # Code / Data
    'py', 'js', 'html', 'css', 'json', 'xml', 'md', 'yml', 'yaml'
])

# Video and audio format mappings for better MIME type support
MIME_TYPE_OVERRIDES = {
    '.mkv': 'video/x-matroska',
    '.webm': 'video/webm',
    '.mov': 'video/quicktime',
    '.wmv': 'video/x-ms-wmv',
    '.flv': 'video/x-flv',
    '.ts': 'video/mp2t',
    '.m4v': 'video/x-m4v',
    '.ogg': 'audio/ogg',
    '.aac': 'audio/aac',
    '.m4a': 'audio/mp4',
    '.aiff': 'audio/aiff',
    '.wma': 'audio/x-ms-wma',
    '.opus': 'audio/opus',
    '.pdf': 'application/pdf',
    '.webp': 'image/webp',
    '.heic': 'image/heic',
    '.bmp': 'image/bmp',
    '.svg': 'image/svg+xml',
    '.tif': 'image/tiff',
    '.tiff': 'image/tiff'
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_bytes(bytes_count):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} TB"

def get_file_info(filepath, is_dir_entry=False, entry=None):
    """
    Get file information.
    If is_dir_entry is True, expects entry to be an os.DirEntry object (optimizes I/O).
    Otherwise, uses os.stat on filepath.
    """
    if is_dir_entry and entry is not None:
        file_size = entry.stat().st_size
        file_ext = os.path.splitext(entry.name)[1].lower()
    else:
        stat = os.stat(filepath)
        file_size = stat.st_size
        file_ext = os.path.splitext(filepath)[1].lower()
    
    # Get file extension and check for MIME type override
    # Optimize by using dict mapping instead of guess_type when possible
    if file_ext in MIME_TYPE_OVERRIDES:
        file_type = MIME_TYPE_OVERRIDES[file_ext]
    elif file_ext in mimetypes.types_map:
        file_type = mimetypes.types_map[file_ext]
    else:
        # Fallback to slower guess_type
        file_type = mimetypes.guess_type(filepath)[0] or 'unknown'
    
    return {
        'size': format_bytes(file_size),
        'type': file_type,
        'is_video': file_type and (file_type.startswith('video/') or file_ext in ['.mkv', '.webm', '.mov', '.wmv', '.flv', '.ts', '.m4v']),
        'is_audio': file_type and (file_type.startswith('audio/') or file_ext in ['.ogg', '.aac', '.m4a']),
        'is_image': file_type and file_type.startswith('image/'),
        'is_pdf': file_ext == '.pdf',
        'extension': file_ext
    }
