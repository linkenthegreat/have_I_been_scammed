-- Enable Foreign Key support for SQLite
PRAGMA foreign_keys = ON;

-- 1. Sessions Table
-- Tracks user interactions to maintain context and history
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_location TEXT,  -- Optional: User's location (e.g., "Australia", "US")
    user_role TEXT       -- Optional: "victim" or "reporter"
);

-- 2. Scam Checks Table (Long-Term Memory)
-- Stores every analysis request and result
CREATE TABLE IF NOT EXISTS scam_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    input_type TEXT NOT NULL CHECK(input_type IN ('text', 'url', 'image', 'audio', 'mixed')),
    input_content TEXT NOT NULL,
    case_summary TEXT,  -- Optional: User's description of what happened
    risk_score TEXT NOT NULL CHECK(risk_score IN ('safe', 'caution', 'high')),
    scam_type TEXT, -- e.g., 'phishing', 'investment', 'romance'
    tags TEXT,      -- Comma-separated keywords e.g., 'urgent,crypto'
    agent_reasoning TEXT, -- JSON string details
    full_response TEXT, -- Complete agent response with formatted email
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 3. Feedback Table (Agent Evaluation)
-- Stores user feedback on analysis quality
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_id INTEGER NOT NULL,
    helpful BOOLEAN NOT NULL,
    false_positive BOOLEAN DEFAULT 0,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (check_id) REFERENCES scam_checks(check_id)
);

-- 4. Metrics Table (Observability)
-- Aggregated stats for dashboarding
CREATE TABLE IF NOT EXISTS metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Observability Events Table (Phase 3)
-- Detailed workflow tracking for agent execution, tool calls, and performance
CREATE TABLE IF NOT EXISTS observability_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('agent_call', 'tool_call', 'error', 'performance', 'workflow')),
    agent_name TEXT,
    tool_name TEXT,
    duration_ms INTEGER,
    input_data TEXT,           -- JSON string
    output_data TEXT,          -- JSON string
    error_message TEXT,
    metadata TEXT,             -- JSON string for custom fields
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_obs_session ON observability_events(session_id);
CREATE INDEX IF NOT EXISTS idx_obs_type ON observability_events(event_type);
CREATE INDEX IF NOT EXISTS idx_obs_timestamp ON observability_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_obs_agent ON observability_events(agent_name);

