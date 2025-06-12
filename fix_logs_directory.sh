#!/bin/bash

# Toyota Dashboard - Fix Logs Directory
# This script creates the missing logs directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_step "Fixing logs directory issue..."

# Check if the application directory exists
if [[ ! -d "/opt/toyota-dashboard" ]]; then
    print_error "Toyota Dashboard not found in /opt/toyota-dashboard"
    print_info "Please run the installation script first"
    exit 1
fi

cd /opt/toyota-dashboard

# Stop the service
print_step "Stopping toyota-dashboard service..."
systemctl stop toyota-dashboard || true

# Create logs directory
if [[ ! -d "logs" ]]; then
    print_step "Creating logs directory..."
    sudo -u toyota mkdir -p logs
    print_success "Logs directory created"
else
    print_info "Logs directory already exists"
fi

# Start the service
print_step "Starting toyota-dashboard service..."
systemctl start toyota-dashboard

# Check service status
sleep 3
if systemctl is-active --quiet toyota-dashboard; then
    print_success "Toyota Dashboard service is running!"
else
    print_error "Service failed to start. Check logs with: sudo journalctl -u toyota-dashboard -f"
    exit 1
fi

print_success "Logs directory issue fixed successfully!"
print_info "Check service status: sudo systemctl status toyota-dashboard"
print_info "View logs: sudo journalctl -u toyota-dashboard -f"