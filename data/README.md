# Data & Storage 💾

Database schemas and datasets for the Scam Prevention Tool.

## Files
- `schema.sql`: SQL schema defining database tables.
- `sample_scams.json`: Test dataset for evaluation.
- `scam_detection.db`: SQLite database (gitignored).
- `adk_sessions.db`: ADK session storage database (gitignored).

### Database Tables

#### `sessions` (scam_detection.db)
Tracks user sessions with timestamps and context:
- `session_id` (TEXT PRIMARY KEY): Unique session identifier
- `created_at` (TIMESTAMP): Session creation time
- `last_accessed` (TIMESTAMP): Last activity time
- `user_location` (TEXT): User's location for personalized reporting
- `user_role` (TEXT): User's role/context (optional)

**Purpose**: Session persistence and user context tracking

#### `scam_checks` (scam_detection.db)
Stores analysis results with comprehensive details:
- `check_id` (INTEGER PRIMARY KEY): Unique analysis identifier
- `session_id` (TEXT): Associated session
- `input_type` (TEXT): 'text', 'url', 'image', 'audio', or 'mixed'
- `input_content` (TEXT): Original input content
- `risk_score` (TEXT): 'SAFE', 'CAUTION', or 'HIGH'
- `scam_type` (TEXT): Identified scam category
- `confidence_score` (REAL): Detection confidence (0.0-1.0)
- `analysis_result` (TEXT): Full JSON analysis results
- `created_at` (TIMESTAMP): Analysis timestamp
- `case_summary` (TEXT): User-provided case description
- `tags` (TEXT): JSON array of relevant tags

**Purpose**: Long-term analysis history and pattern tracking

#### `feedback` (scam_detection.db)
Logs user feedback for agent evaluation:
- `feedback_id` (INTEGER PRIMARY KEY): Unique feedback identifier
- `check_id` (INTEGER): Related analysis
- `feedback_type` (TEXT): 'helpful', 'not_helpful', 'false_positive', etc.
- `comments` (TEXT): Optional user comments
- `created_at` (TIMESTAMP): Feedback timestamp

**Purpose**: Agent evaluation and improvement tracking

#### `metrics` (scam_detection.db)
Aggregated system performance metrics:
- `metric_id` (INTEGER PRIMARY KEY): Unique metric identifier
- `metric_name` (TEXT): Metric type
- `metric_value` (REAL): Measured value
- `timestamp` (TIMESTAMP): Measurement time
- `metadata` (TEXT): JSON additional context

**Purpose**: System-wide performance monitoring

#### `observability_events` (scam_detection.db)
Detailed event tracking for debugging and monitoring:
- `id` (INTEGER PRIMARY KEY): Unique event identifier
- `timestamp` (TIMESTAMP): Event occurrence time
- `session_id` (TEXT): Associated session
- `event_type` (TEXT): 'agent_call', 'tool_call', 'error', 'performance', 'workflow'
- `agent_name` (TEXT): Agent that triggered event
- `tool_name` (TEXT): Tool that was called
- `duration_ms` (INTEGER): Execution duration
- `input_data` (TEXT): JSON input parameters
- `output_data` (TEXT): JSON output results
- `error_message` (TEXT): Error details if applicable
- `metadata` (TEXT): JSON additional context

**Purpose**: Detailed observability, debugging, and performance analysis

**Indexes:**
- `idx_obs_session`: Fast session-based queries
- `idx_obs_type`: Filter by event type
- `idx_obs_timestamp`: Time-based analysis

#### ADK Session Tables (adk_sessions.db)
Managed by Google ADK's `DatabaseSessionService`:
- Session state storage
- Conversation history
- Agent coordination state
- Tool context preservation

**Purpose**: ADK framework's internal session management

## Usage

### Database Inspection
```bash
# List all tables and record counts
python db_cli.py --tables

# View recent sessions
python db_cli.py --sessions --limit 20

# View recent scam checks
python db_cli.py --checks --limit 10

# Get database statistics
python db_cli.py --stats

# Verify database integrity
python db_cli.py --verify
```

### Session Management
Sessions persist across server restarts when `USE_DATABASE_SESSIONS=True`:
- User context maintained (location, role)
- Conversation history preserved
- Analysis history accessible
- Tool state consistent

## Requirements
- SQLite3 (built-in with Python)

## References
- SQLite Documentation: https://www.sqlite.org/docs.html
- Schema Definition: `schema.sql`
- Database Tools: `../agents_n_tools/tools/db_tools.py`
- CLI Tool: `../db_cli.py`
