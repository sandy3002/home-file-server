# Home File Server

A self-hosted web file server built with Flask that lets you browse, upload, download, stream, and manage files from any device on your network — or anywhere on the internet via Cloudflare Tunnel.

## Features

- **Authentication**: User registration and login with bcrypt-hashed passwords stored in MongoDB
- **File Browsing**: Navigate through directories with a clean file browser UI
- **File Upload**: Drag-and-drop or click-to-browse uploads with progress tracking; supports multi-file uploads
- **File Download**: One-click downloads for any file type
- **File Deletion**: Delete files or empty folders via the browser
- **Folder Management**: Create new folders from the browser UI
- **Media Streaming**: In-browser video and audio streaming with HTTP Range request support
- **MPV Integration**: Generate mpv commands or `.m3u` playlist files to play media in the native mpv player
- **Image Preview**: View images directly in the browser
- **PDF Preview**: Inline PDF viewing
- **Security Headers**: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `HSTS` applied on every response
- **Responsive Design**: Works on desktop, tablet, and mobile

## Project Structure

```
home-file-server/
├── run.py                      # Entry point – loads .env and starts Flask
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose setup
├── home-file-server.service    # systemd service unit (Ubuntu)
├── cloudflared-config.yml      # Cloudflare Tunnel config template
├── start_server.sh             # Convenience startup script (Linux/macOS)
├── start_server.bat            # Convenience startup script (Windows)
├── data/                       # Default file storage directory (Docker)
└── app/
    ├── __init__.py             # Application factory (create_app)
    ├── config.py               # Config class – reads from environment
    ├── extensions.py           # MongoDB client initialisation
    ├── security.py             # Security headers + login_required decorator
    ├── utils.py                # File type helpers, MIME overrides, format_bytes
    └── routes/
        ├── auth.py             # /login, /register, /logout
        ├── main.py             # / (dashboard index)
        ├── files.py            # /browse, /upload, /download, /api/delete, /api/create_folder
        └── media.py            # /stream, /media, /mpv, /api/mpv/command
```

## Prerequisites

- Python 3.8+
- MongoDB (local or remote)
- pip

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url> home-file-server
cd home-file-server
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Generate a secure secret key and paste it into `.env`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Edit `.env` with your values (see [Configuration](#configuration)).

### 4. Start MongoDB

```bash
# Ubuntu/Debian
sudo systemctl start mongod

# macOS (Homebrew)
brew services start mongodb-community
```

### 5. Run the server

```bash
python run.py
```

The server starts on `http://127.0.0.1:8080` by default.

> To use the convenience script instead: `bash start_server.sh`

## Configuration

All settings are read from environment variables (`.env` file):

| Variable             | Default                        | Description                                             |
|----------------------|--------------------------------|---------------------------------------------------------|
| `SECRET_KEY`         | `dev-key-change-in-production` | Flask session secret — **always change in production**  |
| `MONGODB_URI`        | *(required)*                   | MongoDB connection string (e.g. `mongodb://localhost:27017/`) |
| `UPLOAD_FOLDER`      | `~/Documents/FileServer`       | Directory where uploaded files are stored               |
| `FLASK_ENV`          | `development`                  | `production` disables debug mode and enables secure cookies |
| `HOST`               | `127.0.0.1`                    | IP address to bind on (`0.0.0.0` to expose on network)  |
| `PORT`               | `8080`                         | Port the server listens on                              |
| `MAX_CONTENT_LENGTH` | `10737418240` (10 GB)          | Maximum upload size in bytes                            |

> Relative paths in `UPLOAD_FOLDER` are resolved relative to the project root. `~` is expanded automatically.

## Supported File Types

| Category   | Extensions                                                          |
|------------|---------------------------------------------------------------------|
| Video      | `mp4`, `avi`, `mkv`, `webm`, `mov`, `wmv`, `flv`, `ts`, `m4v`     |
| Audio      | `mp3`, `wav`, `flac`, `ogg`, `aac`, `m4a`, `aiff`, `wma`, `opus`  |
| Images     | `png`, `jpg`, `jpeg`, `gif`, `webp`, `heic`, `bmp`, `svg`, `tif`, `tiff` |
| Documents  | `txt`, `pdf`, `doc`, `docx`, `xls`, `xlsx`, `ppt`, `pptx`, `csv`  |
| Archives   | `zip`, `rar`, `7z`, `tar`, `gz`                                    |
| Code/Data  | `py`, `js`, `html`, `css`, `json`, `xml`, `md`, `yml`, `yaml`     |

## Usage

### Authentication

Visit the server URL and register an account. All routes (except login/register) require authentication.

### Browsing Files

Go to `/browse` to navigate folders. From the browser you can:
- Click folders to navigate into them
- Download any file
- Stream video/audio in-browser or launch in mpv
- Delete files or empty folders
- Create new folders

### Uploading Files

Go to `/upload`, then drag-and-drop files or click to select. You can optionally specify a sub-folder path to organise uploads. Progress is tracked per file.

### Media Streaming

- **In-browser**: Click the play button on a video or audio file to open the built-in player.
- **mpv (external)**: Click the mpv button to get command-line options or download an `.m3u` playlist file.

HTTP Range requests are supported for efficient seeking in large video files.

## API Routes

| Method | Path                          | Description                     |
|--------|-------------------------------|---------------------------------|
| GET    | `/browse[/<path>]`            | File browser                    |
| GET    | `/upload`                     | Upload page                     |
| POST   | `/upload`                     | Upload files (returns JSON)     |
| GET    | `/download/<path>`            | Download a file                 |
| POST   | `/api/delete/<path>`          | Delete file or empty folder     |
| POST   | `/api/create_folder`          | Create a new folder             |
| GET    | `/stream/<path>`              | Render video/audio player page  |
| GET    | `/media/<path>`               | Serve media with Range support  |
| GET    | `/mpv/<path>`                 | Download `.m3u` playlist        |
| GET    | `/api/mpv/command/<path>`     | Get mpv command JSON            |
| GET    | `/login`                      | Login page                      |
| POST   | `/login`                      | Authenticate                    |
| GET    | `/register`                   | Registration page               |
| POST   | `/register`                   | Create account                  |
| GET    | `/logout`                     | Clear session                   |

## Network Access

By default the server binds to `127.0.0.1` (localhost only). To expose it on your local network:

```bash
# In .env
HOST=0.0.0.0
```

Then access from other devices using `http://<YOUR_IP>:8080`.

For internet access, see [UBUNTU_SETUP.md](UBUNTU_SETUP.md) for a full guide using Cloudflare Tunnel.

## Deployment Options

| Method       | Guide                          |
|--------------|-------------------------------|
| Docker       | [DOCKER_README.md](DOCKER_README.md) |
| Ubuntu + systemd + Cloudflare Tunnel | [UBUNTU_SETUP.md](UBUNTU_SETUP.md) |

## Security Considerations

- All file access is sandboxed to `UPLOAD_FOLDER` — path traversal attacks are blocked
- Passwords are hashed with bcrypt via Werkzeug
- In `production` mode, session cookies are `Secure`, `HttpOnly`, and `SameSite=Lax`
- Security headers (`X-Frame-Options`, `X-XSS-Protection`, `HSTS`, `X-Content-Type-Options`) are added to every response
- Only files with allowed extensions can be uploaded
- The Cloudflare Tunnel setup means port 8080 never needs to be publicly exposed

## Troubleshooting

| Problem                        | Solution                                                              |
|-------------------------------|-----------------------------------------------------------------------|
| Port already in use            | Change `PORT` in `.env`                                               |
| MongoDB connection error       | Ensure `mongod` is running and `MONGODB_URI` is correct               |
| Permission denied on upload    | Check read/write permissions on `UPLOAD_FOLDER`                       |
| File type rejected             | Extension not in `ALLOWED_EXTENSIONS` in `app/utils.py`              |
| Large uploads failing          | Increase `MAX_CONTENT_LENGTH` in `.env`                               |
| Video not seeking properly     | Ensure the browser supports the format; try the mpv option            |

## Development

```bash
# Run with auto-reload (FLASK_ENV=development is set by default)
python run.py
```

To use Gunicorn in production:

```bash
pip install gunicorn
gunicorn -w 2 -b 127.0.0.1:8080 "app:create_app()"
```

## License

Open source. Feel free to modify and distribute as needed.
