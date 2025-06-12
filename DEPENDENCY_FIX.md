# Toyota Dashboard - Dependency Fix

## Problem Description

The Toyota Dashboard service is failing to start with the following error:

```
ModuleNotFoundError: No module named 'jwt'
```

This error occurs because the `PyJWT` library is missing from the Python environment where the application is running.

## Root Cause

The issue is caused by missing dependencies in the `requirements.txt` file. The following dependencies were missing:

1. **pyjwt** - Required for JWT token handling (used in `pytoyoda/controller.py`)
2. **arrow** - Required for date/time handling (used in `pytoyoda/models/vehicle.py`)
3. **langcodes** - Required for locale handling (used in `pytoyoda/utils/locale.py`)

These dependencies are listed in `pyproject.toml` but were missing from `requirements.txt`, which is used by the installation script.

## Solution

### Option 1: Quick Fix (Recommended)

Run the provided fix script on your Raspberry Pi:

```bash
sudo bash fix_dependencies.sh
```

This script will:
1. Stop the toyota-dashboard service
2. Install the missing dependencies in the virtual environment
3. Verify the installation
4. Restart the service

### Option 2: Manual Fix

If you prefer to fix it manually:

1. **Stop the service:**
   ```bash
   sudo systemctl stop toyota-dashboard
   ```

2. **Navigate to the application directory:**
   ```bash
   cd /opt/toyota-dashboard
   ```

3. **Install missing dependencies:**
   ```bash
   sudo -u toyota bash -c "
       source venv/bin/activate
       pip install pyjwt==2.8.0 arrow==1.3.0 langcodes==3.4.0
   "
   ```

4. **Start the service:**
   ```bash
   sudo systemctl start toyota-dashboard
   ```

5. **Check the status:**
   ```bash
   sudo systemctl status toyota-dashboard
   ```

### Option 3: Reinstall Dependencies

If you want to reinstall all dependencies from the updated requirements.txt:

1. **Stop the service:**
   ```bash
   sudo systemctl stop toyota-dashboard
   ```

2. **Update the requirements.txt file** (copy the updated version from this repository)

3. **Reinstall all dependencies:**
   ```bash
   cd /opt/toyota-dashboard
   sudo -u toyota bash -c "
       source venv/bin/activate
       pip install --upgrade pip
       pip install -r requirements.txt
   "
   ```

4. **Start the service:**
   ```bash
   sudo systemctl start toyota-dashboard
   ```

## Verification

After applying the fix, verify that the service is running correctly:

1. **Check service status:**
   ```bash
   sudo systemctl status toyota-dashboard
   ```

2. **View real-time logs:**
   ```bash
   sudo journalctl -u toyota-dashboard -f
   ```

3. **Test JWT import:**
   ```bash
   cd /opt/toyota-dashboard
   sudo -u toyota bash -c "
       source venv/bin/activate
       python3 -c 'import jwt; print(\"JWT version:\", jwt.__version__)'
   "
   ```

## Updated Dependencies

The following dependencies have been added to `requirements.txt`:

```
# Security (updated)
pyjwt==2.8.0

# Date/time handling (updated)
arrow==1.3.0

# Validation and utilities (updated)
langcodes==3.4.0
```

## Prevention

To prevent this issue in the future:

1. Always ensure that `requirements.txt` and `pyproject.toml` dependencies are synchronized
2. Test the installation in a clean environment before deployment
3. Use dependency management tools like Poetry for better consistency

## Troubleshooting

If the service still fails to start after applying the fix:

1. **Check the full error log:**
   ```bash
   sudo journalctl -u toyota-dashboard --no-pager
   ```

2. **Verify Python environment:**
   ```bash
   cd /opt/toyota-dashboard
   sudo -u toyota bash -c "source venv/bin/activate && python3 --version && pip list"
   ```

3. **Check file permissions:**
   ```bash
   ls -la /opt/toyota-dashboard/
   ```

4. **Verify configuration:**
   ```bash
   sudo -u toyota cat /opt/toyota-dashboard/config.yaml
   ```

## Contact

If you continue to experience issues after applying this fix, please:

1. Check the GitHub repository for updates
2. Create an issue with the full error logs
3. Include your system information (OS, Python version, etc.)