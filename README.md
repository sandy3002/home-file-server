# Home File Server Dashboard

A web-based home file server that allows you to manage files and stream media content from your old PC.

## Features

- **File Management**: Browse, upload, download, and delete files
- **Media Streaming**: Stream videos and audio files directly in your browser
- **Folder Management**: Create and organize folders
- **Drag & Drop Upload**: Easy file uploads with progress tracking
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Security**: File access is restricted to the designated server directory

## Installation

1. **Clone or download this project** to your old PC that will serve as the file server

2. **Install Python** (3.7 or higher) if not already installed

3. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Edit the server settings** in `app.py` if needed:

   - `UPLOAD_FOLDER`: Change the directory where files are stored (default: `~/Documents/FileServer`)
   - `app.config['SECRET_KEY']`: Change to a secure random string
   - Host and port settings in the `app.run()` call

2. **Create the file storage directory:**
   ```bash
   mkdir -p ~/Documents/FileServer
   ```

## Running the Server

1. **Start the server:**

   ```bash
   python app.py
   ```

2. **Access the dashboard:**
   - On the same computer: http://localhost:5000
   - From other devices on your network: http://YOUR_PC_IP:5000
   - To find your PC's IP address:
     - Windows: `ipconfig`
     - macOS/Linux: `ifconfig` or `ip addr show`

## Usage

### Dashboard

- View server statistics and quick actions
- Access all main features from the sidebar

### Browse Files

- Navigate through folders
- View file information (type, size)
- Download files by clicking the download button
- Stream videos and audio by clicking the play button
- Delete files and empty folders
- Create new folders

### Upload Files

- Drag and drop files onto the upload zone
- Or click to browse and select files
- Organize files by specifying a folder path
- Monitor upload progress
- Supported formats: MP4, AVI, MKV (video), MP3, WAV, FLAC (audio), JPG, PNG, GIF (images), TXT, PDF (documents)

### Media Streaming

- **Video Player**: Full-featured video player with speed controls, keyboard shortcuts, and fullscreen support
- **Audio Player**: Audio player with visualization, speed controls, and keyboard shortcuts
- **Keyboard Shortcuts**:
  - Space: Play/Pause
  - Arrow keys: Seek (←/→) and volume (↑/↓)
  - F: Fullscreen (videos)
  - M: Mute (audio)

## Network Access

To access your file server from other devices on your network:

1. **Find your PC's local IP address**
2. **Make sure your firewall allows connections on port 5000**
3. **Access from other devices using**: http://YOUR_PC_IP:5000

### Security Considerations

- This server is designed for local network use
- Files are stored in a designated directory to prevent access to system files
- For internet access, consider setting up a VPN or using additional security measures
- Change the default secret key before deployment

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `app.py` (line with `app.run()`)
2. **Permission denied**: Ensure the user has read/write permissions to the upload folder
3. **Large file uploads failing**: Adjust `MAX_CONTENT_LENGTH` in `app.py`
4. **Video/audio not playing**: Ensure your browser supports the media format

### File Size Limits

- Default maximum file size: 1GB per file
- To change: Modify `app.config['MAX_CONTENT_LENGTH']` in `app.py`

## Supported File Types

- **Video**: MP4, AVI, MKV
- **Audio**: MP3, WAV, FLAC
- **Images**: JPG, JPEG, PNG, GIF
- **Documents**: TXT, PDF

## Development

To run in development mode with debug enabled, the server automatically restarts when you make changes to the code.

To run in production:

1. Set `debug=False` in `app.py`
2. Consider using a production WSGI server like Gunicorn
3. Set up proper logging and error handling

## License

This project is open source. Feel free to modify and distribute as needed.
