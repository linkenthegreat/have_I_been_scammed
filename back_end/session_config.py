"""
Session configuration for ADK Runner.
Provides both InMemory (dev/testing) and Database (production) session services.

Usage:
    from back_end.session_config import get_session_service
    
    # For production (persistent sessions)
    session_service = get_session_service(use_database=True)
    
    # For testing (temporary sessions)
    session_service = get_session_service(use_database=False)
"""
import os
import sqlite3
from pathlib import Path
from google.adk.sessions import InMemorySessionService, DatabaseSessionService

# Database path
DB_DIR = Path(__file__).parent.parent / 'data'
SESSION_DB = DB_DIR / 'adk_sessions.db'

def get_session_service(use_database=None):
    """
    Returns appropriate session service based on configuration.
    
    Args:
        use_database: If True, use DatabaseSessionService (persistent).
                      If False, use InMemorySessionService (temporary).
                      If None, read from environment variable USE_DATABASE_SESSIONS.
    
    Returns:
        SessionService instance (InMemorySessionService or DatabaseSessionService)
    """
    if use_database is None:
        # Read from environment
        use_database = os.getenv('USE_DATABASE_SESSIONS', 'True').lower() == 'true'
    
    if use_database:
        # Ensure database directory exists
        DB_DIR.mkdir(exist_ok=True)
        
        # Initialize database schema if needed
        _init_session_database()
        
        print(f"📊 Using DatabaseSessionService: {SESSION_DB}")
        # Use sqlite+aiosqlite for async support
        return DatabaseSessionService(
            db_url=f"sqlite+aiosqlite:///{SESSION_DB}"
        )
    else:
        print("⚠️  Using InMemorySessionService (sessions will be lost on restart)")
        return InMemorySessionService()

def _init_session_database():
    """Initialize session database schema if not exists."""
    if SESSION_DB.exists():
        return  # Already initialized
    
    conn = sqlite3.connect(SESSION_DB)
    cursor = conn.cursor()
    
    # ADK DatabaseSessionService expects specific schema
    # Note: ADK handles the schema internally, but we create the file
    # The actual table creation is done by DatabaseSessionService
    
    conn.commit()
    conn.close()
    
    print(f"✅ Initialized session database: {SESSION_DB}")

# For backwards compatibility (if imported directly)
session_service = get_session_service()