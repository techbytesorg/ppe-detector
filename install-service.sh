#!/bin/bash

# PPE Detector Service Installation Script
# This script installs the PPE detector as a systemd service

set -e

SERVICE_NAME="ppe-detector"
SERVICE_FILE="ppe-detector.service"
INSTALL_DIR="/home/vagrant/source/ppe-detector"
SYSTEMD_DIR="/etc/systemd/system"

echo "🔧 Installing PPE Detector Service..."

# Check if we're in the right directory
if [[ ! -f "$SERVICE_FILE" ]]; then
    echo "❌ Error: $SERVICE_FILE not found. Please run this script from the ppe-detector directory."
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo "❌ Error: Virtual environment 'venv' not found."
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements-jetson.txt"
    exit 1
fi

# Check if main.py exists
if [[ ! -f "main.py" ]]; then
    echo "❌ Error: main.py not found."
    exit 1
fi

# Stop service if it's already running
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🛑 Stopping existing $SERVICE_NAME service..."
    sudo systemctl stop "$SERVICE_NAME"
fi

# Copy service file to systemd directory
echo "📝 Installing service file..."
sudo cp "$SERVICE_FILE" "$SYSTEMD_DIR/"

# Set proper permissions
sudo chmod 644 "$SYSTEMD_DIR/$SERVICE_FILE"

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service to start on boot
echo "✅ Enabling $SERVICE_NAME service..."
sudo systemctl enable "$SERVICE_NAME"

# Start the service
echo "🚀 Starting $SERVICE_NAME service..."
sudo systemctl start "$SERVICE_NAME"

# Check status
sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ $SERVICE_NAME service installed and started successfully!"
    echo ""
    echo "Service commands:"
    echo "  Start:   sudo systemctl start $SERVICE_NAME"
    echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
    echo "  Restart: sudo systemctl restart $SERVICE_NAME"
    echo "  Status:  sudo systemctl status $SERVICE_NAME"
    echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "The PPE detector will now start automatically on boot."
else
    echo "❌ Service failed to start. Check logs:"
    echo "  sudo journalctl -u $SERVICE_NAME -n 20"
    exit 1
fi