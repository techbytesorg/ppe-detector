#!/bin/bash

# PPE Detector Service Uninstallation Script
# This script removes the PPE detector systemd service

set -e

SERVICE_NAME="ppe-detector"
SERVICE_FILE="ppe-detector.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "🗑️  Uninstalling PPE Detector Service..."

# Stop service if it's running
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "🛑 Stopping $SERVICE_NAME service..."
    sudo systemctl stop "$SERVICE_NAME"
fi

# Disable the service
if systemctl is-enabled --quiet "$SERVICE_NAME"; then
    echo "❌ Disabling $SERVICE_NAME service..."
    sudo systemctl disable "$SERVICE_NAME"
fi

# Remove service file
if [[ -f "$SYSTEMD_DIR/$SERVICE_FILE" ]]; then
    echo "🗑️  Removing service file..."
    sudo rm "$SYSTEMD_DIR/$SERVICE_FILE"
fi

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Reset failed state if any
sudo systemctl reset-failed "$SERVICE_NAME" 2>/dev/null || true

echo "✅ $SERVICE_NAME service uninstalled successfully!"
echo ""
echo "The PPE detector will no longer start automatically on boot."
echo "You can still run it manually with: python main.py"