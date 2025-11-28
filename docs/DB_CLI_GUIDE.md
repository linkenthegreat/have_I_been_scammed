# DB CLI Quick Reference Guide

**Tool**: `db_cli.py`  
**Purpose**: Database inspection and log management for developers  
**Location**: Project root directory

---

## 🚀 Quick Start

```bash
# Show help
python db_cli.py --help

# Default view (stats + tables)
python db_cli.py
```

---

## 📊 Database Operations

### List Tables
```bash
python db_cli.py --tables
```
Shows all database tables with record counts.

### View Sessions
```bash
# Recent 10 sessions (default)
python db_cli.py --sessions

# Recent 50 sessions
python db_cli.py --sessions --limit 50
```
Displays session IDs, timestamps, location, and role.

### View Scam Checks
```bash
# Recent 10 checks (default)
python db_cli.py --checks

# Recent 100 checks
python db_cli.py --checks --limit 100

# Checks for specific session
python db_cli.py --session-checks SESSION_ID_HERE
```
Shows analysis results with risk scores and types.

### View Specific Check Details
```bash
python db_cli.py --check-details 5
```
Full details for check ID 5 including JSON analysis.

### View Feedback
```bash
python db_cli.py --feedback --limit 20
```
Shows user feedback on analyses.

### View Metrics
```bash
python db_cli.py --metrics --limit 30
```
System performance metrics.

### Database Statistics
```bash
python db_cli.py --stats
```
Record counts and database health overview.

### Verify Database Integrity
```bash
python db_cli.py --verify
```
Checks foreign key constraints and data consistency.

---

## 📄 Log Management

### List Log Files
```bash
python db_cli.py --logs
```
Shows all log files with sizes and last modified dates.

**Example Output**:
```
📄 Log Files in C:\...\logs:
+-------------------+---------+---------------------+
| File              | Size    | Last Modified       |
+===================+=========+=====================+
| adk_debug.log     | 2.34 MB | 2025-11-29 03:35:19 |
| observability.log | 0.11 MB | 2025-11-29 03:39:55 |
+-------------------+---------+---------------------+

📊 Total size: 2.45 MB (2 files)
```

### View Log Contents (Tail)
```bash
# Last 50 lines of observability.log (default)
python db_cli.py --tail

# Last 100 lines
python db_cli.py --tail --lines 100

# Different log file
python db_cli.py --tail --file adk_debug.log --lines 200
```

**Tip**: Great for quickly checking recent activity without opening files.

### Clean Logs (with Backup)
```bash
python db_cli.py --clean-logs
```

**What happens**:
1. Shows files to be cleaned and total size
2. Asks for confirmation
3. Creates `.bak` backup of each file
4. Empties log files (adds "cleaned" timestamp)
5. Reports space freed

**Example**:
```
🗑️  Log Cleanup
================================================================
Files to clean: 2
Total size: 2.45 MB
Backup: Yes (will create .bak files)

⚠️  Continue? (yes/no): yes

  ✓ Backed up: adk_debug.log → adk_debug.log.bak
  ✓ Cleaned: adk_debug.log
  ✓ Backed up: observability.log → observability.log.bak
  ✓ Cleaned: observability.log

✅ Cleanup complete!
   Cleaned: 2 files
   Backed up: 2 files
   Freed: ~2.45 MB
```

### Clean Logs (No Backup)
```bash
python db_cli.py --clean-logs --no-backup
```
⚠️ **Warning**: Permanent deletion without backups. Use with caution!

### Delete Old Backups
```bash
python db_cli.py --delete-backups
```
Removes all `.bak` backup files to free up disk space.

---

## 💡 Common Workflows

### Daily Development Routine
```bash
# 1. Check system health
python db_cli.py --stats

# 2. View recent activity
python db_cli.py --tail --lines 30

# 3. Check recent checks
python db_cli.py --checks --limit 5
```

### Debugging a Session
```bash
# 1. Find session ID
python db_cli.py --sessions --limit 20

# 2. View session's checks
python db_cli.py --session-checks abc123-session-id

# 3. Get check details
python db_cli.py --check-details 42
```

### Weekly Maintenance
```bash
# 1. Check log sizes
python db_cli.py --logs

# 2. Clean if logs > 50MB
python db_cli.py --clean-logs

# 3. Verify database health
python db_cli.py --verify
```

### Preparing for Demo/Testing
```bash
# 1. Clean logs for fresh start
python db_cli.py --clean-logs

# 2. Verify database integrity
python db_cli.py --verify

# 3. Check current state
python db_cli.py --stats
```

---

## 🔧 Troubleshooting

### "Database not found"
**Problem**: `scam_detection.db` doesn't exist  
**Solution**: Run Flask app first to initialize database
```bash
python back_end/app.py
```

### "No log files found"
**Problem**: `logs/` directory empty or doesn't exist  
**Solution**: Run Flask app to create logs, or:
```bash
mkdir logs
```

### "UnicodeEncodeError" when tailing logs
**Problem**: Windows console encoding issues  
**Solution**: The tool now handles this automatically with multiple encoding fallbacks

### Can't clean logs - permission denied
**Problem**: Log files in use by running server  
**Solution**: Stop Flask server first:
```bash
# PowerShell
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force
```

---

## 📋 Command Reference Table

| Command | Purpose | Common Options |
|---------|---------|----------------|
| `--tables` | List all tables | - |
| `--sessions` | View sessions | `--limit N` |
| `--checks` | View checks | `--limit N` |
| `--check-details ID` | Check details | - |
| `--session-checks SID` | Session checks | - |
| `--feedback` | View feedback | `--limit N` |
| `--metrics` | View metrics | `--limit N` |
| `--stats` | Database stats | - |
| `--verify` | Verify integrity | - |
| `--logs` | List log files | - |
| `--tail` | View log tail | `--file`, `--lines` |
| `--clean-logs` | Clean logs | `--no-backup` |
| `--delete-backups` | Delete .bak files | - |

---

## 🎯 Best Practices

### Development
- ✅ Check `--stats` before and after major changes
- ✅ Use `--tail` to monitor real-time activity
- ✅ Clean logs weekly during active development
- ✅ Always use `--verify` after schema changes

### Testing
- ✅ Clean logs before test runs for clear output
- ✅ Use `--session-checks` to verify test sessions
- ✅ Check `--feedback` to validate test scenarios

### Production
- ✅ Schedule weekly `--clean-logs` (with backup)
- ✅ Monitor `--logs` for disk space
- ✅ Run `--verify` monthly
- ✅ Review `--metrics` for performance trends

### Debugging
- ✅ Start with `--tail` to see recent activity
- ✅ Use `--check-details` for full analysis context
- ✅ Combine `--sessions` and `--session-checks` for user flow
- ✅ Check `adk_debug.log` for LLM request/response details

---

## 📚 Related Documentation

- Main README: `../README.md`
- Database Schema: `../data/README.md`
- Observability Guide: `../adk_notebook/observability_google_adk.md`
- Backend API: `../back_end/README.md`

---

## 🆘 Need Help?

```bash
# Full help with examples
python db_cli.py --help

# Check database exists
ls data/*.db

# Check logs exist
ls logs/*.log

# Test basic functionality
python db_cli.py --tables
```

---

**Last Updated**: November 29, 2025  
**Version**: 1.0  
**Status**: Production Ready
