# Home File Server

A self-hosted web file server built with Flask that lets you browse, upload, download, stream, and manage files from any device on your network — or anywhere on the internet if you use Cloudflare Tunnel.

## Features

- Login/Register available (user creation and management will be coming next)
- Upload, Download, Browse files.
- In-browser image, pdf, video and audio streaming available

## Prerequisites

- Python 3.8+
- MongoDB (local or remote)

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

### 4. Run the server

```bash
python run.py
```

The server starts on `http://127.0.0.1:8080` by default.

## Configuration

All settings are read from environment variables (`.env` file):

| Variable             | Default                        | Description                                                   |
| -------------------- | ------------------------------ | ------------------------------------------------------------- |
| `SECRET_KEY`         | `dev-key-change-in-production` | Flask session secret — **always change in production**        |
| `MONGODB_URI`        | _(required)_                   | MongoDB connection string (e.g. `mongodb://localhost:27017/`) |
| `UPLOAD_FOLDER`      | `~/Documents/FileServer`       | Directory where uploaded files are stored                     |
| `FLASK_ENV`          | `development`                  | `production` disables debug mode and enables secure cookies   |
| `HOST`               | `127.0.0.1`                    | IP address to bind on (`0.0.0.0` to expose on network)        |
| `PORT`               | `8080`                         | Port the server listens on                                    |
| `MAX_CONTENT_LENGTH` | `10737418240` (10 GB)          | Maximum upload size in bytes                                  |

> Relative paths in `UPLOAD_FOLDER` are resolved relative to the project root. `~` is expanded automatically.

## Usage

### Authentication

Visit the server URL and register an account. All routes require authentication.

### Browsing Files

Go to `/browse` to navigate folders. From the browser you can:

### Uploading Files

Go to `/upload`, then drag-and-drop files or click to select. You can optionally specify a sub-folder path to organise uploads. Progress is tracked per file.

### Media Streaming

In-browser streaming is supported for video and audio files.

## Network Access

By default the server binds to `127.0.0.1` (localhost only). To expose it on your local network:

```bash
# In .env
HOST=0.0.0.0
```

Then access from other devices using `http://<YOUR_IP>:8080`.

## License

Open source. Feel free to modify and distribute as you wish.

## Disclaimer

This project is created by AI and me.
