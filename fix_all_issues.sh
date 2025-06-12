#!/bin/bash

# Toyota Dashboard - Fix All Issues
# This script fixes both dependency and version issues

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
    echo "║                Toyota Dashboard Fix All Issues              ║"
    echo "║              Исправление всех проблем                       ║"
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

cd /opt/toyota-dashboard

# Stop the service
print_step "Stopping toyota-dashboard service..."
systemctl stop toyota-dashboard || true

# Fix dependencies
print_step "Installing missing dependencies..."
sudo -u toyota bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    
    # Install critical dependencies
    echo 'Installing PyJWT...'
    pip install pyjwt==2.8.0
    
    echo 'Installing Arrow...'
    pip install arrow==1.3.0
    
    echo 'Installing Langcodes...'
    pip install langcodes==3.4.0
    
    # Verify installation
    echo 'Verifying dependencies:'
    python3 -c 'import jwt; print(\"✓ PyJWT:\", jwt.__version__)'
    python3 -c 'import arrow; print(\"✓ Arrow:\", arrow.__version__)'
    python3 -c 'import langcodes; print(\"✓ Langcodes installed\")'
    
    echo 'All dependencies installed successfully'
" || {
    print_error "Error installing dependencies"
    exit 1
}

# Create logs directory if missing
if [[ ! -d "logs" ]]; then
    print_step "Creating logs directory..."
    sudo -u toyota mkdir -p logs
    print_success "Logs directory created"
fi

# Fix version issue
if [[ -f "pytoyoda/__init__.py" ]]; then
    print_step "Fixing version error in pytoyoda/__init__.py..."
    # Create backup
    cp pytoyoda/__init__.py pytoyoda/__init__.py.backup
    
    # Fix the version line
    sed -i 's/from importlib_metadata import version/# from importlib_metadata import version/' pytoyoda/__init__.py
    sed -i 's/__version__ = version(__name__)/__version__ = "0.0.0"/' pytoyoda/__init__.py
    
    print_success "Version error fixed"
else
    print_error "pytoyoda/__init__.py not found"
    exit 1
fi

# Verify all fixes
print_step "Verifying all fixes..."
sudo -u toyota bash -c "
    cd /opt/toyota-dashboard
    source venv/bin/activate
    python3 -c 'from pytoyoda import MyT; print(\"✓ PyToyoda import successful\")'
    python3 -c 'import jwt, arrow, langcodes; print(\"✓ All dependencies working\")'
" || {
    print_error "Verification failed"
    # Restore backup if available
    if [[ -f "pytoyoda/__init__.py.backup" ]]; then
        cp pytoyoda/__init__.py.backup pytoyoda/__init__.py
        print_info "Backup restored"
    fi
    exit 1
}

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

print_success "All issues fixed successfully!"
echo
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                        SUCCESS!                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo
print_info "Toyota Dashboard is now running properly"
print_info "Access your dashboard at: http://$(hostname -I | awk '{print $1}')"
print_info "Check service status: sudo systemctl status toyota-dashboard"
print_info "View logs: sudo journalctl -u toyota-dashboard -f"
echo