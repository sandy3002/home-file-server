# Home File Server - Docker Setup

This application is now containerized with Docker! Here are the different ways to run it:

## Quick Start with Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The application will be available at http://localhost:8080

## Manual Docker Commands

```bash
# Build the image
docker build -t home-file-server .

# Run the container
docker run -d \
  --name home-file-server \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  home-file-server

# View logs
docker logs -f home-file-server

# Stop and remove container
docker stop home-file-server
docker rm home-file-server
```

## File Storage

- Files are stored in the `./data` directory on your host machine
- This directory is automatically created and mounted to the container
- Your files persist even when the container is stopped or removed

## Environment Variables

You can customize the application using environment variables:

- `UPLOAD_FOLDER`: Path inside container for file storage (default: `/app/data`)

## Development Mode

To run in development mode with live code reloading:

```bash
# Create a development docker-compose override
cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  home-file-server:
    volumes:
      - .:/app
      - ./data:/app/data
    environment:
      - FLASK_ENV=development
    command: python app.py
EOF

# Start in development mode
docker-compose up
```

## Health Check

The container includes a health check that verifies the application is running properly. Check the health status:

```bash
docker ps  # Shows health status in the STATUS column
```

## Security Notes

- The container runs as a non-root user for security
- File operations are restricted to the mounted data directory
- The application is configured for production use by default

## Accessing from Other Devices

The server binds to all interfaces (0.0.0.0), so you can access it from other devices on your network using your computer's IP address:

- Find your IP: `docker-compose exec home-file-server hostname -I`
- Access via: `http://YOUR_IP:8080`
