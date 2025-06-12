#!/bin/bash

# Toyota Dashboard - Fix Read-only Filesystem Issue
# This script fixes the read-only filesystem issue and sets up proper logging

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

print_header() {
    echo
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           Toyota Dashboard - Fix Filesystem Issues          ║"
    echo "║              Исправление проблем файловой системы           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_header

# Check if the application directory exists
if [[ ! -d "/opt/toyota-dashboard" ]]; then
    print_error "Toyota Dashboard not found in /opt/toyota-dashboard"
    print_info "Please run the installation script first"
    exit 1
fi

# Stop the service
print_step "Stopping toyota-dashboard service..."
systemctl stop toyota-dashboard || true

# Check filesystem status
print_step "Checking filesystem status..."
if mount | grep -q "/ .*ro,"; then
    print_warning "Root filesystem is mounted read-only!"
    print_step "Attempting to remount as read-write..."
    mount -o remount,rw / || {
        print_error "Failed to remount filesystem as read-write"
        print_info "You may need to:"
        print_info "1. Check SD card for errors: sudo fsck /dev/mmcblk0p2"
        print_info "2. Reboot the system: sudo reboot"
        exit 1
    }
    print_success "Filesystem remounted as read-write"
else
    print_info "Filesystem is already read-write"
fi

# Check disk space
print_step "Checking disk space..."
df_output=$(df -h / | tail -1)
echo "Disk usage: $df_output"
available_space=$(echo "$df_output" | awk '{print $4}' | sed 's/[^0-9]//g')
if [[ $available_space -lt 100 ]]; then
    print_warning "Low disk space detected (less than 100MB available)"
    print_info "Consider cleaning up old files or expanding storage"
fi

# Ensure proper permissions for log directory
print_step "Setting up log directory permissions..."
mkdir -p /var/log/toyota-dashboard
chown -R toyota:toyota /var/log/toyota-dashboard
chmod 755 /var/log/toyota-dashboard
print_success "Log directory permissions set"

# Ensure proper permissions for application directory
print_step "Setting up application directory permissions..."
chown -R toyota:toyota /opt/toyota-dashboard
chmod 755 /opt/toyota-dashboard
print_success "Application directory permissions set"

# Create a test log file to verify write permissions
print_step "Testing write permissions..."
sudo -u toyota touch /var/log/toyota-dashboard/test.log && rm /var/log/toyota-dashboard/test.log
print_success "Write permissions verified"

# Update app.py to use system log directory (if not already updated)
cd /opt/toyota-dashboard
if grep -q "logs/toyota-dashboard.log" app.py; then
    print_step "Updating app.py to use system log directory..."
    sudo -u toyota sed -i "s|'logs/toyota-dashboard.log'|'/var/log/toyota-dashboard/app.log'|g" app.py
    sudo -u toyota sed -i "s|os.makedirs('logs', exist_ok=True)|log_dir = '/var/log/toyota-dashboard'; os.makedirs(log_dir, exist_ok=True)|g" app.py
    print_success "App.py updated to use system log directory"
fi

# Start the service
print_step "Starting toyota-dashboard service..."
systemctl start toyota-dashboard

# Check service status
sleep 3
if systemctl is-active --quiet toyota-dashboard; then
    print_success "Toyota Dashboard service is running!"
    print_info "Service status: $(systemctl is-active toyota-dashboard)"
else
    print_error "Service failed to start. Check logs with: sudo journalctl -u toyota-dashboard -f"
    exit 1
fi

print_success "Filesystem issues fixed successfully!"
echo
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                        SUCCESS!                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo
print_info "Toyota Dashboard is now running properly"
print_info "Application logs: tail -f /var/log/toyota-dashboard/app.log"
print_info "System logs: sudo journalctl -u toyota-dashboard -f"
print_info "Check service status: sudo systemctl status toyota-dashboard"
echo

# Additional recommendations
print_info "Recommendations to prevent future issues:"
print_info "1. Regularly check disk space: df -h"
print_info "2. Monitor system logs: sudo journalctl -f"
print_info "3. Consider using log rotation: logrotate"
print_info "4. Check SD card health periodically"