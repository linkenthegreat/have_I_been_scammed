import json
from datetime import datetime
from google.adk.tools.tool_context import ToolContext
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "scam_detection.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ADK-Compatible Tools (with ToolContext)

def log_scam_check(
    tool_context: ToolContext,
    session_id: str,
    input_type: str,
    content: str,
    risk_score: str,
    scam_type: str = None,
    tags: str = None,
    reasoning: str = None,
    confidence: float = 0.0
) -> dict:
    """
    Logs a scam analysis result to session state and database.
    
    Args:
        tool_context: ADK ToolContext (auto-injected)
        session_id: Session identifier (must be passed explicitly)
        input_type: Type of input ('text', 'url', 'image', 'audio', 'mixed')
        content: The content that was analyzed
        risk_score: Risk assessment ('safe', 'caution', 'danger')
        scam_type: Type of scam detected (optional)
        tags: Comma-separated tags (optional)
        reasoning: JSON string containing analysis reasoning (not dict)
        confidence: Confidence score 0.0-1.0 (optional)
    """
    try:
        print(f"DEBUG 1: Received session_id = {repr(session_id)}")
        
        if not session_id or session_id == "None":
            print("DEBUG 2: Returning error (session_id is missing or invalid)")
            return {
                "status": "error",
                "error": "Invalid session_id",
                "message": "Session ID is required but was not provided"
            }
        
        print("DEBUG 3: Validation passed, continuing...")
        
        # Parse reasoning JSON string if provided
        reasoning_dict = None
        if reasoning:
            try:
                reasoning_dict = json.loads(reasoning)
            except json.JSONDecodeError:
                # If not valid JSON, wrap as raw text
                reasoning_dict = {"raw_reasoning": reasoning}
        
        # Store in ADK session state (short-term)
        check_data = {
            "input_type": input_type,
            "content": content,
            "risk_score": risk_score,
            "scam_type": scam_type,
            "tags": tags,
            "reasoning": reasoning_dict,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to session state
        check_key = f"check:{int(datetime.now().timestamp())}"
        tool_context.state[check_key] = check_data
        
        # Also log to custom DB for analytics
        check_id = _persist_to_db(session_id, check_data)
        print(f"DEBUG 4: Database insert succeeded, check_id = {check_id}")
        
        return {
            "status": "success",
            "check_id": check_id,
            "message": "Scam check logged successfully",
            "session_state_key": check_key
        }
    except Exception as e:
        print(f"DEBUG 5: Exception: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to log scam check"
        }

def get_recent_checks(tool_context: ToolContext, limit: int = 5) -> dict:
    """
    Retrieves recent checks from session state.
    
    Args:
        tool_context: ADK ToolContext (auto-injected)
        limit: Maximum number of checks to retrieve
        
    Returns:
        dict: List of recent checks
    """
    try:
        # Get checks from session state
        checks = []
        for key, value in tool_context.state.items():
            if key.startswith("check:"):
                # Validate that value is a dict (skip corrupted data)
                if isinstance(value, dict):
                    checks.append(value)
                else:
                    # Log warning but don't crash
                    print(f"WARNING: Corrupted check data at key {key}: {type(value)}")
        
        # Sort by timestamp and limit
        checks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        checks = checks[:limit]
        
        return {
            "status": "success",
            "checks": checks,
            "count": len(checks)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "checks": [],
            "count": 0
        }

def update_session_context(
    tool_context: ToolContext,
    user_location: str = None,
    user_role: str = None
) -> dict:
    """
    Updates user context in session state.
    
    Args:
        tool_context: ADK ToolContext (auto-injected)
        user_location: User's location (e.g., "Australia")
        user_role: User's role ("victim", "reporter", "other")
        
    Returns:
        dict: Status message
    """
    try:
        if user_location:
            tool_context.state["user:location"] = user_location
        if user_role:
            tool_context.state["user:role"] = user_role
        
        return {
            "status": "success",
            "message": "Session context updated",
            "location": user_location,
            "role": user_role
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to update session context"
        }

def get_session_context(tool_context: ToolContext) -> dict:
    """
    Retrieves user context from session state.
    
    Args:
        tool_context: ADK ToolContext (auto-injected)
        
    Returns:
        dict: User location and role
    """
    try:
        return {
            "status": "success",
            "location": tool_context.state.get("user:location"),
            "role": tool_context.state.get("user:role")
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "location": None,
            "role": None
        }

# Non-ADK wrapper for backend usage
def update_session_context_direct(session_id, user_location=None, user_role=None):
    """
    Updates user context directly from backend (bypassing ADK ToolContext).
    Used by Flask app.py.
    """
    # For now, we only persist to DB if we had a sessions table column update
    # But since we store context in sessions table, we should update it there
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ensure session exists first
    create_session(session_id)
    
    if user_location and user_role:
        cursor.execute("""
            UPDATE sessions 
            SET user_location = ?, user_role = ? 
            WHERE session_id = ?
        """, (user_location, user_role, session_id))
    elif user_location:
        cursor.execute("""
            UPDATE sessions 
            SET user_location = ? 
            WHERE session_id = ?
        """, (user_location, session_id))
    elif user_role:
        cursor.execute("""
            UPDATE sessions 
            SET user_role = ? 
            WHERE session_id = ?
        """, (user_role, session_id))
        
    conn.commit()
    conn.close()
    return {"status": "success"}

# Non-ADK wrapper for backend usage
def log_check_direct(session_id, input_type, content, risk_score, scam_type=None, tags=None, reasoning=None, confidence=0.0, full_response=None):
    """
    Logs a scam check directly from the backend (bypassing ADK ToolContext).
    Used by OrchestratorService.
    """
    check_data = {
        "input_type": input_type,
        "content": content,
        "risk_score": risk_score,
        "scam_type": scam_type,
        "tags": tags,
        "reasoning": reasoning,
        "confidence": confidence,
        "full_response": full_response
    }
    return _persist_to_db(session_id, check_data)

# Internal helper (not exposed as tool)
def _persist_to_db(session_id: str, check_data: dict) -> int:
    """Persists check data to SQLite for analytics (internal use)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO scam_checks 
        (session_id, input_type, input_content, risk_score, scam_type, tags, agent_reasoning, full_response, confidence_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        check_data["input_type"],
        check_data["content"],
        check_data["risk_score"],
        check_data["scam_type"],
        check_data["tags"],
        json.dumps(check_data["reasoning"]) if check_data.get("reasoning") else None,
        check_data.get("full_response"),
        check_data["confidence"]
    ))
    
    check_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return check_id

def get_recent_checks_direct(session_id: str, limit: int = 5) -> list:
    """
    Retrieves recent scam checks from the database for a specific session.
    Used for long-term memory context in agents.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT input_content, risk_score, scam_type, created_at 
            FROM scam_checks 
            WHERE session_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "content": row["input_content"],
                "risk": row["risk_score"],
                "type": row["scam_type"],
                "date": row["created_at"]
            })
        return history
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []

# Non-ADK utility functions (for Flask routes, testing, etc.)
def create_session(session_id: str) -> str:
    """Creates a session if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO sessions (session_id) VALUES (?)
    """, (session_id,))
    conn.commit()
    conn.close()
    return session_id

def get_check(check_id):
    """
    Retrieves a scam check record by its ID.
    
    Args:
        check_id (int): The check ID to retrieve
        
    Returns:
        dict: {
            "status": "success" | "not_found" | "error",
            "check": dict | None,
            "message": str
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM scam_checks WHERE check_id = ?
        """, (check_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "status": "success",
                "check": dict(row),
                "message": f"Found check ID {check_id}",
                # Flatten for easier access if needed, but keeping structure clean
                **dict(row) 
            }
        else:
            return {
                "status": "not_found",
                "check": None,
                "message": f"Check ID {check_id} not found"
            }
    except Exception as e:
        return {
            "status": "error",
            "check": None,
            "message": f"Error retrieving check: {str(e)}"
        }

def add_feedback(check_id: int, helpful: bool, false_positive: bool = False, comments: str = None):
    """Records user feedback for a specific check (called from Flask route)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (check_id, helpful, false_positive, comments)
        VALUES (?, ?, ?, ?)
    """, (check_id, helpful, false_positive, comments))
    conn.commit()
    conn.close()

def init_db():
    """Initializes the database tables if they don't exist (matches schema.sql)."""
    # Ensure data directory exists
    data_dir = DB_PATH.parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
    cursor = conn.cursor()
    
    # 1. Sessions Table (MUST be created first - referenced by scam_checks)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_location TEXT,
            user_role TEXT
        )
    """)
    
    # 2. Scam Checks Table (Long-Term Memory)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scam_checks (
            check_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            input_type TEXT NOT NULL CHECK(input_type IN ('text', 'url', 'image', 'audio', 'mixed')),
            input_content TEXT NOT NULL,
            case_summary TEXT,
            risk_score TEXT NOT NULL CHECK(risk_score IN ('safe', 'caution', 'high')),
            scam_type TEXT,
            tags TEXT,
            agent_reasoning TEXT,
            confidence_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # 3. Feedback Table (Agent Evaluation)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_id INTEGER NOT NULL,
            helpful BOOLEAN NOT NULL,
            false_positive BOOLEAN DEFAULT 0,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (check_id) REFERENCES scam_checks(check_id)
        )
    """)
    
    # 4. Metrics Table (Observability)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scam_checks_session 
        ON scam_checks(session_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scam_checks_created 
        ON scam_checks(created_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_check 
        ON feedback(check_id)
    """)
    
    conn.commit()
    conn.close()
