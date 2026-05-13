# Home File Server — Docker Setup

Run the Home File Server in a fully isolated Docker container with persistent file storage.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)
- A running MongoDB instance (local or remote — see note below)

> **Note:** The Docker image runs the Flask application only. MongoDB is **not** bundled in the image. You must supply a `MONGODB_URI` pointing to an external MongoDB instance (local host, another container, or MongoDB Atlas).

## Quick Start (Docker Compose)

### 1. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```env
SECRET_KEY=<your-secure-random-key>
MONGODB_URI=mongodb://host.docker.internal:27017/   # local MongoDB on the host
UPLOAD_FOLDER=/app/data                             # path inside the container
FLASK_ENV=production
HOST=0.0.0.0
PORT=8080
```

> Use `host.docker.internal` to reach MongoDB running on the host machine from inside the container.

### 2. Build and start

```bash
docker-compose up -d
```

The application is available at **http://localhost:8080**

### 3. Useful commands

```bash
# View live logs
docker-compose logs -f

# Restart the container
docker-compose restart

# Stop and remove the container
docker-compose down
```

## Manual Docker Commands

```bash
# Build the image
docker build -t home-file-server .

# Run the container
docker run -d \
  --name home-file-server \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  -e UPLOAD_FOLDER=/app/data \
  home-file-server

# View logs
docker logs -f home-file-server

# Stop and remove
docker stop home-file-server
docker rm home-file-server
```

## File Storage

- Files are stored in the `./data/` directory on the **host** machine.
- This directory is mounted into the container at `/app/data`.
- Files **persist** even when the container is stopped or removed.
- To use an existing directory: edit the volume in `docker-compose.yml`:
  ```yaml
  volumes:
    - /your/existing/path:/app/data
  ```

## Environment Variables

All variables from `.env` are passed into the container via `env_file`. Key variables:

| Variable             | Value inside container | Description                              |
|----------------------|------------------------|------------------------------------------|
| `SECRET_KEY`         | *(your value)*         | Flask session secret                     |
| `MONGODB_URI`        | *(your value)*         | MongoDB connection string                |
| `UPLOAD_FOLDER`      | `/app/data`            | File storage path (keep as `/app/data`)  |
| `FLASK_ENV`          | `production`           | Disables debug mode                      |
| `HOST`               | `0.0.0.0`              | Bind on all interfaces                   |
| `PORT`               | `8080`                 | Port exposed by the container            |
| `MAX_CONTENT_LENGTH` | `10737418240`          | Max upload size (10 GB default)          |

## Health Check

The container checks that the application is responding every 30 seconds:

```bash
# Check health status
docker ps                               # Shows HEALTHY / UNHEALTHY in STATUS column

# Inspect health details
docker inspect --format='{{json .State.Health}}' home-file-server
```

## Development Mode (Live Code Reload)

Create a `docker-compose.override.yml` to mount the source code and enable auto-reload:

```yaml
services:
  home-file-server:
    volumes:
      - .:/app
      - ./data:/app/data
    environment:
      - FLASK_ENV=development
    command: python run.py
```

Then start normally:

```bash
docker-compose up
```

## Security Notes

- The container runs as a **non-root user** (`appuser`) for security.
- File operations are restricted to the `/app/data` mount — path traversal is blocked at the application level.
- Security response headers (`X-Frame-Options`, `X-XSS-Protection`, `HSTS`, `X-Content-Type-Options`) are set by the app on every request.
- In `FLASK_ENV=production`, session cookies are `Secure`, `HttpOnly`, and `SameSite=Lax`.

## Accessing from Other Devices

The server binds to `0.0.0.0` by default in the Docker setup, so other devices on your network can reach it:

```bash
# Find your host machine's IP
ip addr show          # Linux
ifconfig              # macOS

# Access from another device
http://<HOST_IP>:8080
```

## Stopping and Cleanup

```bash
# Stop container (data is preserved)
docker-compose down

# Remove container AND delete stored files
docker-compose down
rm -rf ./data
```
