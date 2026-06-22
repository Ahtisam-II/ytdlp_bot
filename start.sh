#!/bin/bash
# start.sh - Script to start the bot and keep it running

# Make sure we are in the script's directory
cd "$(dirname "$0")"

# Check if python is installed
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install it using 'pkg install python'"
    exit 1
fi

# Create downloads directory if it doesn't exist
mkdir -p downloads

echo "Starting Telegram yt-dlp Bot..."
while true; do
    python main.py
    echo "Bot crashed or exited. Restarting in 5 seconds..."
    sleep 5
done
