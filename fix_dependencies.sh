#!/bin/bash

# Toyota Dashboard - Fix Missing Dependencies
# This script fixes the missing JWT and other dependencies issue

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
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

print_step "Fixing Toyota Dashboard dependencies..."

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

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    print_warning "Virtual environment not found, creating one..."
    sudo -u toyota python3 -m venv venv
fi

# Install missing dependencies
print_step "Installing missing dependencies..."
sudo -u toyota bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install pyjwt==2.8.0
    pip install arrow==1.3.0
    pip install langcodes==3.4.0
" || {
    print_error "Failed to install dependencies"
    exit 1
}

# Verify JWT installation
print_step "Verifying JWT installation..."
sudo -u toyota bash -c "
    source venv/bin/activate
    python3 -c 'import jwt; print(\"JWT version:\", jwt.__version__)'
" || {
    print_error "JWT verification failed"
    exit 1
}

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

print_success "Dependencies fixed successfully!"
print_info "You can check the service status with: sudo systemctl status toyota-dashboard"
print_info "View logs with: sudo journalctl -u toyota-dashboard -f"