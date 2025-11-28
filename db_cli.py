#!/usr/bin/env python3
"""
Database CLI Tool for Scam Detection Database
Inspect, verify, and manage database records.
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
import json
import os
import shutil

# Database path
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "scam_detection.db"
LOGS_DIR = BASE_DIR / "logs"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        print("   Run the Flask app first to initialize the database.")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def list_tables():
    """List all tables in the database."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print("\n📊 Database Tables:")
    print("=" * 60)
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table['name']}")
        count = cursor.fetchone()['count']
        print(f"  • {table['name']}: {count} records")
    
    conn.close()

def show_sessions(limit=10):
    """Display recent sessions."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT session_id, created_at, last_accessed, user_location, user_role
        FROM sessions
        ORDER BY last_accessed DESC
        LIMIT {limit}
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("\n📭 No sessions found.")
        conn.close()
        return
    
    print(f"\n🔑 Recent Sessions (Last {limit}):")
    print("=" * 60)
    
    data = []
    for row in rows:
        data.append([
            row['session_id'][:20] + "..." if len(row['session_id']) > 20 else row['session_id'],
            row['created_at'],
            row['last_accessed'],
            row['user_location'] or 'N/A',
            row['user_role'] or 'N/A'
        ])
    
    print(tabulate(data, headers=['Session ID', 'Created', 'Last Accessed', 'Location', 'Role'], tablefmt='grid'))
    conn.close()

def show_scam_checks(limit=10, session_id=None):
    """Display recent scam checks."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    if session_id:
        cursor.execute("""
            SELECT check_id, session_id, input_type, input_content, risk_score, 
                   scam_type, confidence_score, created_at
            FROM scam_checks
            WHERE session_id = ?
            ORDER BY created_at DESC
        """, (session_id,))
    else:
        cursor.execute(f"""
            SELECT check_id, session_id, input_type, input_content, risk_score, 
                   scam_type, confidence_score, created_at
            FROM scam_checks
            ORDER BY created_at DESC
            LIMIT {limit}
        """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("\n📭 No scam checks found.")
        conn.close()
        return
    
    print(f"\n🔍 Recent Scam Checks (Last {limit}):")
    print("=" * 60)
    
    data = []
    for row in rows:
        content = row['input_content'][:40] + "..." if len(row['input_content']) > 40 else row['input_content']
        
        data.append([
            row['check_id'],
            row['session_id'][:15] + "..." if len(row['session_id']) > 15 else row['session_id'],
            row['input_type'],
            content,
            row['risk_score'],
            row['scam_type'] or 'N/A',
            f"{row['confidence_score']:.2f}" if row['confidence_score'] else 'N/A',
            row['created_at']
        ])
    
    print(tabulate(data, headers=['ID', 'Session', 'Type', 'Content', 'Risk', 'Scam Type', 'Confidence', 'Created'], tablefmt='grid'))
    conn.close()

def show_check_details(check_id):
    """Display detailed information about a specific scam check."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM scam_checks
        WHERE check_id = ?
    """, (check_id,))
    
    row = cursor.fetchone()
    
    if not row:
        print(f"\n❌ No scam check found with ID: {check_id}")
        conn.close()
        return
    
    print(f"\n🔍 Scam Check Details (ID: {check_id}):")
    print("=" * 60)
    print(f"Session ID:       {row['session_id']}")
    print(f"Input Type:       {row['input_type']}")
    print(f"Risk Score:       {row['risk_score']}")
    print(f"Scam Type:        {row['scam_type'] or 'N/A'}")
    print(f"Confidence:       {row['confidence_score'] or 'N/A'}")
    print(f"Tags:             {row['tags'] or 'N/A'}")
    print(f"Created At:       {row['created_at']}")
    print(f"\nInput Content:")
    print("-" * 60)
    print(row['input_content'])
    
    if row['case_summary']:
        print(f"\nCase Summary:")
        print("-" * 60)
        print(row['case_summary'])
    
    if row['agent_reasoning']:
        print(f"\nAgent Reasoning:")
        print("-" * 60)
        try:
            reasoning = json.loads(row['agent_reasoning'])
            print(json.dumps(reasoning, indent=2))
        except:
            print(row['agent_reasoning'])
    
    conn.close()

def show_feedback(limit=10):
    """Display recent feedback."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT f.feedback_id, f.check_id, f.helpful, f.false_positive, 
               f.comments, f.created_at
        FROM feedback f
        ORDER BY f.created_at DESC
        LIMIT {limit}
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("\n📭 No feedback found.")
        conn.close()
        return
    
    print(f"\n💬 Recent Feedback (Last {limit}):")
    print("=" * 60)
    
    data = []
    for row in rows:
        data.append([
            row['feedback_id'],
            row['check_id'],
            '✅' if row['helpful'] else '❌',
            '⚠️' if row['false_positive'] else '✓',
            row['comments'][:40] + "..." if row['comments'] and len(row['comments']) > 40 else (row['comments'] or 'N/A'),
            row['created_at']
        ])
    
    print(tabulate(data, headers=['ID', 'Check ID', 'Helpful', 'False Positive', 'Comments', 'Created'], tablefmt='grid'))
    conn.close()

def show_metrics(limit=20):
    """Display recent metrics."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT metric_name, metric_value, recorded_at
        FROM metrics
        ORDER BY recorded_at DESC
        LIMIT {limit}
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("\n📭 No metrics found.")
        conn.close()
        return
    
    print(f"\n📈 Recent Metrics (Last {limit}):")
    print("=" * 60)
    
    data = []
    for row in rows:
        data.append([
            row['metric_name'],
            f"{row['metric_value']:.2f}",
            row['recorded_at']
        ])
    
    print(tabulate(data, headers=['Metric Name', 'Value', 'Recorded At'], tablefmt='grid'))
    conn.close()

def show_stats():
    """Display database statistics."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    print("\n📊 Database Statistics:")
    print("=" * 60)
    
    # Total counts
    cursor.execute("SELECT COUNT(*) as count FROM sessions")
    sessions_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM scam_checks")
    checks_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM feedback")
    feedback_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM metrics")
    metrics_count = cursor.fetchone()['count']
    
    print(f"  Total Sessions:     {sessions_count}")
    print(f"  Total Scam Checks:  {checks_count}")
    print(f"  Total Feedback:     {feedback_count}")
    print(f"  Total Metrics:      {metrics_count}")
    
    # Risk score distribution
    cursor.execute("""
        SELECT risk_score, COUNT(*) as count
        FROM scam_checks
        GROUP BY risk_score
    """)
    risk_dist = cursor.fetchall()
    
    if risk_dist:
        print("\n  Risk Score Distribution:")
        for row in risk_dist:
            print(f"    • {row['risk_score']}: {row['count']}")
    
    # Input type distribution
    cursor.execute("""
        SELECT input_type, COUNT(*) as count
        FROM scam_checks
        GROUP BY input_type
    """)
    input_dist = cursor.fetchall()
    
    if input_dist:
        print("\n  Input Type Distribution:")
        for row in input_dist:
            print(f"    • {row['input_type']}: {row['count']}")
    
    # Scam type distribution
    cursor.execute("""
        SELECT scam_type, COUNT(*) as count
        FROM scam_checks
        WHERE scam_type IS NOT NULL
        GROUP BY scam_type
        ORDER BY count DESC
        LIMIT 5
    """)
    scam_dist = cursor.fetchall()
    
    if scam_dist:
        print("\n  Top Scam Types:")
        for row in scam_dist:
            print(f"    • {row['scam_type']}: {row['count']}")
    
    conn.close()

def verify_database():
    """Verify database integrity and structure."""
    conn = get_db_connection()
    if not conn:
        return
    
    print("\n🔍 Verifying Database Integrity:")
    print("=" * 60)
    
    cursor = conn.cursor()
    
    # Check if all tables exist
    required_tables = ['sessions', 'scam_checks', 'feedback', 'metrics']
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row['name'] for row in cursor.fetchall()]
    
    print("\n1️⃣ Checking required tables...")
    all_tables_exist = True
    for table in required_tables:
        if table in existing_tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} (missing)")
            all_tables_exist = False
    
    # Check foreign key integrity
    print("\n2️⃣ Checking foreign key integrity...")
    cursor.execute("PRAGMA foreign_key_check")
    fk_violations = cursor.fetchall()
    
    if fk_violations:
        print(f"   ❌ Found {len(fk_violations)} foreign key violations")
        for violation in fk_violations:
            print(f"      {violation}")
    else:
        print("   ✅ No foreign key violations")
    
    # Check for orphaned records
    print("\n3️⃣ Checking for orphaned records...")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM scam_checks
        WHERE session_id NOT IN (SELECT session_id FROM sessions)
    """)
    orphaned_checks = cursor.fetchone()['count']
    
    if orphaned_checks > 0:
        print(f"   ⚠️  Found {orphaned_checks} orphaned scam_checks records")
    else:
        print("   ✅ No orphaned scam_checks records")
    
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM feedback
        WHERE check_id NOT IN (SELECT check_id FROM scam_checks)
    """)
    orphaned_feedback = cursor.fetchone()['count']
    
    if orphaned_feedback > 0:
        print(f"   ⚠️  Found {orphaned_feedback} orphaned feedback records")
    else:
        print("   ✅ No orphaned feedback records")
    
    print("\n" + "=" * 60)
    if all_tables_exist and not fk_violations and orphaned_checks == 0 and orphaned_feedback == 0:
        print("✅ Database integrity check passed!")
    else:
        print("⚠️  Database has some issues (see above)")
    
    conn.close()

def list_log_files():
    """List all log files with their sizes."""
    if not LOGS_DIR.exists():
        print(f"\n❌ Logs directory not found at: {LOGS_DIR}")
        return
    
    log_files = list(LOGS_DIR.glob("*.log*"))
    
    if not log_files:
        print(f"\n📭 No log files found in {LOGS_DIR}")
        return
    
    print(f"\n📄 Log Files in {LOGS_DIR}:")
    print("=" * 80)
    
    data = []
    total_size = 0
    
    for log_file in sorted(log_files):
        size = log_file.stat().st_size
        size_mb = size / (1024 * 1024)
        total_size += size
        
        modified = datetime.fromtimestamp(log_file.stat().st_mtime)
        
        data.append([
            log_file.name,
            f"{size_mb:.2f} MB",
            modified.strftime("%Y-%m-%d %H:%M:%S")
        ])
    
    print(tabulate(data, headers=['File', 'Size', 'Last Modified'], tablefmt='grid'))
    print(f"\n📊 Total size: {total_size / (1024 * 1024):.2f} MB ({len(log_files)} files)")

def clean_logs(backup=True, confirm=True):
    """Clean all log files with optional backup."""
    if not LOGS_DIR.exists():
        print(f"\n❌ Logs directory not found at: {LOGS_DIR}")
        return
    
    log_files = list(LOGS_DIR.glob("*.log*"))
    
    if not log_files:
        print(f"\n📭 No log files found to clean")
        return
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in log_files)
    total_size_mb = total_size / (1024 * 1024)
    
    print(f"\n🗑️  Log Cleanup")
    print("=" * 80)
    print(f"Files to clean: {len(log_files)}")
    print(f"Total size: {total_size_mb:.2f} MB")
    
    if backup:
        print(f"Backup: Yes (will create .bak files)")
    else:
        print(f"Backup: No (permanent deletion)")
    
    if confirm:
        response = input("\n⚠️  Continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("❌ Cancelled")
            return
    
    # Perform cleanup
    cleaned_count = 0
    backed_up_count = 0
    
    for log_file in log_files:
        try:
            if backup:
                backup_file = log_file.with_suffix(log_file.suffix + '.bak')
                shutil.copy2(log_file, backup_file)
                backed_up_count += 1
                print(f"  ✓ Backed up: {log_file.name} → {backup_file.name}")
            
            # Clear the log file (keep it but empty)
            with open(log_file, 'w') as f:
                f.write(f"# Log cleaned on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            cleaned_count += 1
            print(f"  ✓ Cleaned: {log_file.name}")
            
        except Exception as e:
            print(f"  ❌ Error cleaning {log_file.name}: {e}")
    
    print("\n✅ Cleanup complete!")
    print(f"   Cleaned: {cleaned_count} files")
    if backup:
        print(f"   Backed up: {backed_up_count} files")
    print(f"   Freed: ~{total_size_mb:.2f} MB")

def delete_log_backups():
    """Delete all .bak backup files."""
    if not LOGS_DIR.exists():
        print(f"\n❌ Logs directory not found at: {LOGS_DIR}")
        return
    
    backup_files = list(LOGS_DIR.glob("*.bak"))
    
    if not backup_files:
        print(f"\n📭 No backup files found")
        return
    
    total_size = sum(f.stat().st_size for f in backup_files)
    total_size_mb = total_size / (1024 * 1024)
    
    print(f"\n🗑️  Delete Log Backups")
    print("=" * 80)
    print(f"Backup files: {len(backup_files)}")
    print(f"Total size: {total_size_mb:.2f} MB")
    
    response = input("\n⚠️  Permanently delete backups? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Cancelled")
        return
    
    deleted_count = 0
    for backup_file in backup_files:
        try:
            backup_file.unlink()
            deleted_count += 1
            print(f"  ✓ Deleted: {backup_file.name}")
        except Exception as e:
            print(f"  ❌ Error deleting {backup_file.name}: {e}")
    
    print(f"\n✅ Deleted {deleted_count} backup files (~{total_size_mb:.2f} MB freed)")

def tail_log(filename="observability.log", lines=50):
    """Show last N lines of a log file."""
    log_file = LOGS_DIR / filename
    
    if not log_file.exists():
        print(f"\n❌ Log file not found: {log_file}")
        return
    
    print(f"\n📄 Last {lines} lines of {filename}:")
    print("=" * 80)
    
    try:
        # Try UTF-8 first, fall back to system encoding
        encodings = ['utf-8', 'latin-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(log_file, 'r', encoding=encoding, errors='replace') as f:
                    all_lines = f.readlines()
                    break
            except UnicodeDecodeError:
                continue
        
        if all_lines:
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            for line in last_lines:
                print(line.rstrip())
            
            print("\n" + "=" * 80)
            print(f"Showing {len(last_lines)} of {len(all_lines)} total lines")
        else:
            print("❌ Could not read log file")
        
    except Exception as e:
        print(f"❌ Error reading log: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Database CLI Tool for Scam Detection Database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Database Operations:
    %(prog)s --tables                    # List all tables
    %(prog)s --sessions                  # Show recent sessions
    %(prog)s --checks                    # Show recent scam checks
    %(prog)s --check-details 5           # Show details for check ID 5
    %(prog)s --feedback                  # Show recent feedback
    %(prog)s --metrics                   # Show recent metrics
    %(prog)s --stats                     # Show database statistics
    %(prog)s --verify                    # Verify database integrity
  
  Log Management:
    %(prog)s --logs                      # List all log files
    %(prog)s --tail                      # Show last 50 lines of observability.log
    %(prog)s --tail --file adk_debug.log --lines 100  # Custom log tail
    %(prog)s --clean-logs                # Clean logs (with backup)
    %(prog)s --clean-logs --no-backup    # Clean logs (no backup)
    %(prog)s --delete-backups            # Delete .bak backup files
        """
    )
    
    # Database operations
    parser.add_argument('--tables', action='store_true', help='List all tables')
    parser.add_argument('--sessions', action='store_true', help='Show recent sessions')
    parser.add_argument('--checks', action='store_true', help='Show recent scam checks')
    parser.add_argument('--check-details', type=int, metavar='ID', help='Show details for a specific check')
    parser.add_argument('--session-checks', type=str, metavar='SESSION_ID', help='Show checks for a specific session')
    parser.add_argument('--feedback', action='store_true', help='Show recent feedback')
    parser.add_argument('--metrics', action='store_true', help='Show recent metrics')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--verify', action='store_true', help='Verify database integrity')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of records (default: 10)')
    
    # Log management operations
    parser.add_argument('--logs', action='store_true', help='List all log files with sizes')
    parser.add_argument('--tail', action='store_true', help='Show last N lines of a log file')
    parser.add_argument('--file', type=str, default='observability.log', help='Log file name (default: observability.log)')
    parser.add_argument('--lines', type=int, default=50, help='Number of lines to show (default: 50)')
    parser.add_argument('--clean-logs', action='store_true', help='Clean all log files (creates backups by default)')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup when cleaning logs')
    parser.add_argument('--delete-backups', action='store_true', help='Delete all .bak backup files')
    
    args = parser.parse_args()
    
    # If no arguments provided, show stats and tables
    if not any(vars(args).values()) or (args.limit == 10 and len([v for v in vars(args).values() if v]) == 1):
        print("\n🗄️  Scam Detection Database CLI")
        print("=" * 60)
        show_stats()
        list_tables()
        print("\nUse --help for more options")
        return
    
    if args.tables:
        list_tables()
    
    if args.sessions:
        show_sessions(args.limit)
    
    if args.checks:
        show_scam_checks(args.limit)
    
    if args.check_details:
        show_check_details(args.check_details)
    
    if args.session_checks:
        show_scam_checks(limit=100, session_id=args.session_checks)
    
    if args.feedback:
        show_feedback(args.limit)
    
    if args.metrics:
        show_metrics(args.limit)
    
    if args.stats:
        show_stats()
    
    if args.verify:
        verify_database()
    
    # Log management
    if args.logs:
        list_log_files()
    
    if args.tail:
        tail_log(args.file, args.lines)
    
    if args.clean_logs:
        clean_logs(backup=not args.no_backup)
    
    if args.delete_backups:
        delete_log_backups()

if __name__ == "__main__":
    main()
