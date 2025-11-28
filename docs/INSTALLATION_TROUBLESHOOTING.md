# Installation & Troubleshooting Guide

This guide helps you resolve common installation and setup issues.

---

## 📋 Prerequisites Check

### Python Version
```bash
python --version
```
**Required**: Python 3.10 or higher

**Issue**: Version too old  
**Fix**: Download from [python.org](https://www.python.org/downloads/)

### Pip Version
```bash
pip --version
```
**Required**: pip 21.0 or higher

**Issue**: Pip not found or outdated  
**Fix**: 
```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

---

## 🔧 Installation Issues

### Issue: `pip install -r requirements.txt` fails

#### Error: "No module named 'pip'"
**Cause**: pip not installed  
**Fix**:
```bash
python -m ensurepip --default-pip
python -m pip install --upgrade pip
```

#### Error: "Could not find a version that satisfies the requirement..."
**Cause**: Package version conflicts or Python version too old  
**Fix**:
1. Check Python version (must be 3.10+)
2. Upgrade pip: `pip install --upgrade pip`
3. Try installing packages individually:
   ```bash
   pip install flask google-adk google-generativeai
   pip install python-dotenv pytest requests
   pip install fpdf2 sqlalchemy aiosqlite pyyaml tabulate
   ```

#### Error: "Permission denied" (Linux/Mac)
**Cause**: Insufficient permissions  
**Fix**: Use virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### Error: "Microsoft Visual C++ required" (Windows)
**Cause**: Missing C++ build tools  
**Fix**: Download [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

---

## 🐍 Virtual Environment (Recommended)

### Why Use Virtual Environment?
- Isolates project dependencies
- Prevents version conflicts
- Easier to manage different projects

### Setup Virtual Environment

**Windows (PowerShell)**:
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Windows (Command Prompt)**:
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Linux/Mac**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Deactivate Virtual Environment
```bash
deactivate
```

---

## 🔑 API Key Issues

### Issue: "GOOGLE_API_KEY not found"

**Cause**: `.env` file missing or incorrectly configured  
**Fix**:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env  # Linux/Mac
   copy .env.example .env  # Windows
   ```
2. Edit `.env` and add your key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

### Get Google API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key
4. Add to `.env` file

### Issue: "Invalid API key"

**Cause**: Incorrect key format or expired key  
**Fix**:
1. Verify key format (should start with "AIza...")
2. Generate new key from Google AI Studio
3. Check for extra spaces in `.env` file
4. Ensure no quotes around the key:
   ```
   # ✅ Correct
   GOOGLE_API_KEY=AIzaSy...

   # ❌ Wrong
   GOOGLE_API_KEY="AIzaSy..."
   ```

---

## 🗄️ Database Issues

### Issue: "Database not found"

**Cause**: Database not initialized  
**Fix**: Run the app once to create database:
```bash
python back_end/app.py
# Press Ctrl+C after it starts
```

### Issue: "Database is locked"

**Cause**: Multiple processes accessing database  
**Fix**:
```bash
# Stop all Python processes
# Windows:
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force

# Linux/Mac:
pkill python
```

### Issue: "Integrity constraint failed"

**Cause**: Database schema mismatch  
**Fix**: Delete and recreate database:
```bash
rm data/scam_detection.db data/adk_sessions.db
python back_end/app.py
```
⚠️ **Warning**: This deletes all data!

---

## 🚀 Runtime Issues

### Issue: "Port 5000 already in use"

**Cause**: Another app using port 5000  
**Fix**:
```bash
# Find process using port 5000
# Windows:
netstat -ano | findstr :5000

# Linux/Mac:
lsof -i :5000

# Kill the process or use different port
# In app.py, change: app.run(port=5001)
```

### Issue: "ImportError: cannot import name..."

**Cause**: Missing or outdated dependencies  
**Fix**:
```bash
# Verify dependencies
python check_dependencies.py

# Reinstall all dependencies
pip install --upgrade -r requirements.txt
```

### Issue: App crashes immediately

**Cause**: Various possible causes  
**Fix**:
1. Check logs: `python db_cli.py --tail`
2. Run with verbose logging:
   ```bash
   # In .env file:
   LOG_LEVEL=DEBUG
   ```
3. Check console output for errors
4. Verify `.env` file is configured correctly

---

## 🧪 Testing Issues

### Issue: Tests fail with "No module named 'agents_n_tools'"

**Cause**: Python path not configured  
**Fix**:
```bash
# Add project root to PYTHONPATH
# Windows (PowerShell):
$env:PYTHONPATH = "$PWD"

# Linux/Mac:
export PYTHONPATH=$PWD

# Or run from project root:
cd /path/to/have_I_been_scammed
pytest tests/
```

### Issue: "Database connection failed" during tests

**Cause**: Test database not found  
**Fix**: Tests use in-memory database, but if issue persists:
```bash
# Run app once to initialize:
python back_end/app.py
# Then run tests:
pytest tests/ -v
```

---

## 📊 Performance Issues

### Issue: Slow response times

**Possible Causes & Fixes**:

1. **Large log files**:
   ```bash
   python db_cli.py --logs
   python db_cli.py --clean-logs
   ```

2. **Database size**:
   ```bash
   # Check database size
   python db_cli.py --stats
   # Archive old data if needed
   ```

3. **API rate limits**:
   - Add delays between requests
   - Check Google AI quota limits

### Issue: High memory usage

**Fix**: Restart app to clear in-memory caches:
```bash
# Stop app
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force

# Restart
python back_end/app.py
```

---

## 🔍 Debugging Tools

### Check Dependencies
```bash
python check_dependencies.py
```

### View System Health
```bash
curl http://localhost:5000/api/health
# Or visit in browser
```

### Check Database
```bash
python db_cli.py --verify
python db_cli.py --stats
```

### View Logs
```bash
python db_cli.py --tail --lines 100
python db_cli.py --tail --file adk_debug.log --lines 200
```

### Test Specific Component
```bash
# Test database connection
python -c "from agents_n_tools.tools import db_tools; print('✅ DB OK')"

# Test agent loading
python -c "from agents_n_tools import agent; print('✅ Agents OK')"

# Test Flask
python -c "from flask import Flask; print('✅ Flask OK')"
```

---


### Still Having Issues?

1. **Check logs**:
   ```bash
   python db_cli.py --tail --lines 50
   ```

2. **Verify installation**:
   ```bash
   python check_dependencies.py
   ```

3. **Check documentation**:
   - `docs/README.md`
   - `docs/DB_CLI_GUIDE.md`
   - `adk_notebook/observability_google_adk.md`

4. **Create GitHub Issue**:
   Include:
   - Python version
   - Operating system
   - Error message (full traceback)
   - Steps to reproduce

---

---

**Last Updated**: November 29, 2025  
**Version**: 1.0
