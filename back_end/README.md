# Backend API 🔌

Flask application serving the Scam Prevention Tool with orchestrated 7-agent workflow.

## Subdirectories
- `services/`: Business logic and 7-agent orchestration
- `plugins/`: Custom ADK plugins (currently unused - using ADK built-in logging)

### Core Modules

#### `app.py`
Main Flask application entry point with:
- DEBUG-level logging configuration
- RotatingFileHandler for log management (10MB × 5 files)
- ADK and Gemini logger configuration
- Database-backed session management
- Health check and observability endpoints

**Key Routes:**
- `GET /`: Home page (renders `index.html`)
- `POST /api/analyze`: Scam analysis endpoint (accepts content, type, location, role)
- `POST /api/feedback`: User feedback collection
- `GET /api/export/email`: Download analysis as .eml file (accepts check_id)
- `GET /api/export/pdf`: Download analysis as PDF report (accepts check_id)
- `GET /api/health`: System health check endpoint
- `GET /observability`: Observability dashboard
- `GET /api/observability/metrics/<session_id>`: Session-specific metrics
- `GET /api/observability/errors`: Recent errors
- `GET /api/observability/performance`: System-wide performance

**Workflow:**
1. Receives user input + optional context (location, role)
2. Stores context in DatabaseSessionService
3. Orchestrates 7 agents: Orchestrator → Receptionist/Analyzer → Report → Resource → Record
4. Logs all events to observability_events table
5. Returns analysis + personalized reporting contacts

#### `session_config.py`
Session management configuration providing:
- `DatabaseSessionService` for production (persistent sessions)
- `InMemorySessionService` for testing (temporary sessions)
- Automatic database initialization
- Environment-controlled switching (`USE_DATABASE_SESSIONS`)

#### `observability.py`
Observability tracking system with:
- `ObservabilityTracker` class for event logging
- Decorators for automatic agent/tool tracking
- Workflow step monitoring
- Performance metrics collection
- Error tracking with full context

#### `logging_utils.py`
Helper utilities for enhanced logging:
- LLM request/response formatters
- Tool call logging
- PII sanitization functions
- Structured log formatting

#### `memory_config.py`
Memory management for ADK agents:
- Session-based memory configuration
- Conversation history tracking
- State management utilities

### Services

#### `services/orchestrator_service.py`
Orchestrates the 7-agent workflow:
- Creates root OrchestratorAgent with 6 sub-agents
- Manages DatabaseSessionService integration
- Coordinates multi-agent interactions
- Handles session state and context
- Integrates observability tracking

#### `services/export_service.py`
Export functionality for reports:
- `.eml` email generation
- PDF report generation
- Formatted report templates

## Configuration

### Environment Variables (`.env`)
```bash
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional
SAFE_BROWSING_API_KEY=your_safe_browsing_key

# Session Management
USE_DATABASE_SESSIONS=True  # False for in-memory (testing only)

# Logging
LOG_LEVEL=DEBUG  # DEBUG for development, INFO for production

# Flask
FLASK_USE_RELOADER=False  # Disable auto-reload to preserve sessions
```

## Requirements
- `flask`
- `python-dotenv`
- `google-adk`
- `google-generativeai`
- `sqlite3` (built-in)

## Logging

### Log Files
- `logs/adk_debug.log` - Rotating debug logs (10MB × 5 files)
- `logs/observability.log` - Workflow and event tracking

### Log Levels
- **DEBUG**: Full LLM request/response, tool calls, detailed traces
- **INFO**: Standard application events, agent coordination
- **WARNING**: Non-critical issues
- **ERROR**: Failures with stack traces

### Viewing Logs
```bash
# Using db_cli.py
python db_cli.py --tail --file adk_debug.log --lines 100

# Using tail (Linux/Mac)
tail -f logs/adk_debug.log

# Using PowerShell (Windows)
Get-Content logs/adk_debug.log -Tail 50 -Wait
```

## References
- Flask Documentation: https://flask.palletsprojects.com/
- Google ADK Documentation: https://google.github.io/adk-docs/
- Orchestrator Service: `services/orchestrator_service.py`
- Observability Guide: `../adk_notebook/observability_google_adk.md`
