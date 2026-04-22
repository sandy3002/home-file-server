#!/bin/bash

# Home File Server Startup Script

echo "🏠 Starting Home File Server Dashboard..."
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pipx &> /dev/null; then
    echo "❌ pipx is not installed. Please install pip."
    exit 1
fi

# Install requirements if they don't exist
echo "📦 Installing required packages..."
pipx install -r requirements.txt

# Create the file storage directory if it doesn't exist
FILE_DIR="$HOME/Documents/FileServer"
if [ ! -d "$FILE_DIR" ]; then
    echo "📁 Creating file storage directory: $FILE_DIR"
    mkdir -p "$FILE_DIR"
fi

# Get local IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -n1 | awk '{print $2}')
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
else
    # Windows/Other
    LOCAL_IP="localhost"
fi

echo ""
echo "🚀 Starting server..."
echo "📂 Files will be stored in: $FILE_DIR"
echo "🌐 Access dashboard at:"
echo "   • Local:   http://localhost:5000"
if [ "$LOCAL_IP" != "localhost" ]; then
    echo "   • Network: http://$LOCAL_IP:5000"
fi
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="

# Start the Flask application
python3 run.py