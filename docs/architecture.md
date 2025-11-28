# System Architecture 🏗️

Comprehensive technical architecture documentation for the Scam Detection Tool.

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture Pattern](#architecture-pattern)
3. [Component Diagram](#component-diagram)
4. [Agent Architecture](#agent-architecture)
5. [Data Flow](#data-flow)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [External Integrations](#external-integrations)
9. [Session Management](#session-management)
10. [Observability](#observability)
11. [Deployment](#deployment)

---

## Overview

### System Purpose
AI-powered web application for detecting and preventing fraud and scams using multimodal analysis, specialized agents, and real-time threat databases.

### Technology Stack

**Backend**:
- **Language**: Python 3.10+
- **Framework**: Flask
- **AI Framework**: Google ADK (Agent Development Kit)
- **AI Model**: Gemini 2.5 Flash (multimodal, multilingual)

**Database**:
- **Development**: SQLite
- **Production**: PostgreSQL (recommended)
- **ORM**: SQLAlchemy 2.0+

**Frontend**:
- **Template Engine**: Jinja2
- **JavaScript**: Vanilla ES6+
- **CSS**: Custom responsive design

**Testing**:
- **Framework**: pytest
- **Approach**: Test-Driven Development (TDD)

---

## Architecture Pattern

### LLM-Orchestrated Multi-Agent System

```
┌─────────────────────────────────────────────────┐
│         User Request (Web Interface)            │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│              Flask Backend                       │
│  ┌───────────────────────────────────────────┐  │
│  │      OrchestratorService                  │  │
│  │  (Creates Runner + Orchestrator Agent)    │  │
│  └───────────────┬───────────────────────────┘  │
└──────────────────┼──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│           ADK Runner (Single Instance)          │
│  • Session Management                           │
│  • State Tracking                               │
│  • Agent Coordination                           │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│         OrchestratorAgent (Root)                │
│  • LLM-based routing                            │
│  • Dynamic agent selection                      │
│  • Response coordination                        │
└────────────────┬────────────────────────────────┘
                 │
                 ├─────► Sub-Agents (as AgentTools)
                 │
    ┌────────────┼────────────┬───────────┬───────────┬──────────┐
    │            │            │           │           │          │
    ▼            ▼            ▼           ▼           ▼          ▼
┌────────┐  ┌──────┐  ┌──────────┐  ┌────────┐  ┌──────────┐
│Recep-  │  │Text  │  │URL       │  │Report  │  │Resource  │
│tionist │  │Ana-  │  │Analyzer  │  │Genera- │  │Assis-    │
│        │  │lyzer │  │          │  │tor     │  │tant      │
└────────┘  └──────┘  └──────────┘  └────────┘  └──────────┘
```

### Key Design Principles

1. **Single Runner**: One ADK Runner manages all agent coordination
2. **LLM Orchestration**: The orchestrator's LLM decides which agents to invoke
3. **Agent as Tools**: Sub-agents wrapped as `AgentTool` for LLM invocation
4. **State Sharing**: Session context automatically propagated via `ToolContext`
5. **Separation of Concerns**: Each agent has a specific, well-defined role

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  index.html  │  │  script.js   │  │  style.css   │          │
│  │  (Jinja2)    │  │  (ES6+)      │  │  (Responsive)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/JSON
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    app.py (Flask)                        │   │
│  │  • Routes: /, /api/analyze, /api/feedback, /health      │   │
│  │  • Session management                                    │   │
│  │  • Error handling                                        │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                              │
│  ┌────────────────▼─────────────────────────────────────────┐   │
│  │           OrchestratorService                            │   │
│  │  • Creates ADK Runner                                    │   │
│  │  • Manages orchestrator agent                            │   │
│  │  • Handles async processing                              │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                              │
│  ┌────────────────▼─────────────────────────────────────────┐   │
│  │          Session Configuration                           │   │
│  │  • DatabaseSessionService (prod)                         │   │
│  │  • InMemorySessionService (dev/test)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           ObservabilityTracker                           │   │
│  │  • Event logging                                         │   │
│  │  • Performance metrics                                   │   │
│  │  • Dashboard data                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Layer (ADK)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              OrchestratorAgent                           │   │
│  │  • Root agent with LLM coordination                      │   │
│  │  • Contains 5 specialist agents as tools                 │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                              │
│     ┌─────────────┼─────────────┬───────────┬──────────┐        │
│     │             │             │           │          │        │
│  ┌──▼───┐  ┌─────▼──┐  ┌──────▼────┐  ┌───▼────┐  ┌──▼──────┐ │
│  │Recep-│  │Text    │  │URL        │  │Report  │  │Resource │ │
│  │tionist│  │Analyzer│  │Analyzer   │  │Gen.    │  │Assist.  │ │
│  └──────┘  └────────┘  └───────────┘  └────────┘  └─────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Tool Layer                                 │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐             │
│  │ Safe       │  │ URLhaus     │  │ URL Metadata │             │
│  │ Browsing   │  │ Checker     │  │ Extractor    │             │
│  │ API        │  │             │  │              │             │
│  └────────────┘  └─────────────┘  └──────────────┘             │
│                                                                  │
│  ┌────────────┐  ┌─────────────┐                                │
│  │ Google     │  │ Database    │                                │
│  │ Search     │  │ Tools       │                                │
│  │ (ADK)      │  │             │                                │
│  └────────────┘  └─────────────┘                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              SQLite Database                             │   │
│  │  • scam_detection.db (app data)                          │   │
│  │  • adk_sessions.db (session persistence)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Log Files                                   │   │
│  │  • observability.log (rotating, 10MB)                    │   │
│  │  • adk_debug.log (DEBUG level, 10MB)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Agent Architecture

### 5-Agent System

#### 1. OrchestratorAgent (Root)
**Role**: Central coordinator using LLM-based routing

**Responsibilities**:
- Analyze user requests
- Dynamically select appropriate specialist agents
- Coordinate multi-agent workflows
- Compile final responses

**Configuration**: `agents_n_tools/agent_prompts/orchestrator_agent.yaml`

**Sub-Agents** (as AgentTools):
- ReceptionistAgent
- TextAnalyzerAgent
- URLAnalyzerAgent
- ReportGeneratorAgent
- ResourceAssistantAgent

---

#### 2. ReceptionistAgent
**Role**: User interaction and context gathering

**Responsibilities**:
- Welcome users
- Collect optional context (location, role)
- Explain system capabilities
- Maintain conversational flow

**Tools**:
- `update_session_context`: Store user location/role
- `get_session_context`: Retrieve stored context

**Configuration**: `agents_n_tools/agent_prompts/receptionist_agent.yaml`

---

#### 3. TextAnalyzerAgent
**Role**: Text and image scam pattern detection

**Responsibilities**:
- Analyze text messages for scam indicators
- Process screenshots using multimodal capabilities
- Identify urgency tactics, threats, suspicious requests
- Detect grammar anomalies

**Output Key**: `text_analysis_result`

**Configuration**: `agents_n_tools/agent_prompts/text_analyzer_agent.yaml`

---

#### 4. URLAnalyzerAgent
**Role**: URL safety verification

**Responsibilities**:
- Check URLs against Safe Browsing database
- Query URLhaus malware database
- Extract domain metadata (age, registrar, SSL)
- Identify suspicious URL patterns

**Tools**:
- `check_url_safety`: Google Safe Browsing API
- `check_urlhaus`: URLhaus malware database
- `extract_url_metadata`: Domain info extraction

**Output Key**: `url_analysis_result`

**Configuration**: `agents_n_tools/agent_prompts/url_analyzer_agent.yaml`

---

#### 5. ReportGeneratorAgent
**Role**: Compile findings into actionable reports

**Responsibilities**:
- Synthesize analysis results
- Determine risk level (HIGH/MEDIUM/LOW/UNCLEAR)
- Provide clear reasoning
- Suggest actionable steps
- Recommend reporting resources

**Input Keys**: `text_analysis_result`, `url_analysis_result`

**Output Key**: `final_report`

**Configuration**: `agents_n_tools/agent_prompts/report_generator_agent.yaml`

---

#### 6. ResourceAssistantAgent
**Role**: Location-specific resource finder

**Responsibilities**:
- Find local scam reporting contacts
- Provide country-specific guidance
- Search for law enforcement contacts
- Draft email templates for reporting

**Tools**:
- `google_search`: ADK built-in Google Search

**Configuration**: `agents_n_tools/agent_prompts/resource_assistant_agent.yaml`

---

## Data Flow

### Request Processing Flow

```
1. User submits input via web form
   ↓
2. Flask receives POST to /api/analyze
   ↓
3. OrchestratorService.process_user_request() called
   ↓
4. Session created/retrieved (DatabaseSessionService)
   ↓
5. ObservabilityTracker initialized
   ↓
6. ADK Runner invokes OrchestratorAgent
   ↓
7. Orchestrator's LLM analyzes request
   ↓
8. LLM decides which specialist agents to call:
   - Text content? → TextAnalyzerAgent
   - URL found? → URLAnalyzerAgent
   - Need context? → ReceptionistAgent
   ↓
9. Specialist agents execute with their tools
   ↓
10. ReportGeneratorAgent compiles findings
    ↓
11. ResourceAssistantAgent adds local contacts (if needed)
    ↓
12. OrchestratorAgent returns final response
    ↓
13. Backend logs to database and observability
    ↓
14. JSON response sent to frontend
    ↓
15. Frontend displays results with visual indicators
```

### Session State Flow

```
Session Creation:
├─ DatabaseSessionService.create_session()
├─ Stored in adk_sessions.db
└─ Session ID returned

Context Update:
├─ ReceptionistAgent calls update_session_context
├─ Stored in ToolContext.session.state
└─ Persisted across requests

Context Retrieval:
├─ Any agent calls get_session_context
├─ Retrieved from ToolContext.session.state
└─ Available to all agents in same session
```

---

## Database Schema

### Main Database: `scam_detection.db`

#### `sessions` Table
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    last_active TEXT NOT NULL,
    user_location TEXT,
    user_role TEXT,
    status TEXT DEFAULT 'active'
);
```

#### `scam_checks` Table
```sql
CREATE TABLE scam_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    input_type TEXT NOT NULL,
    user_input TEXT NOT NULL,
    analysis_result TEXT,
    risk_level TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

#### `feedback` Table
```sql
CREATE TABLE feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    helpful BOOLEAN,
    comments TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (check_id) REFERENCES scam_checks(check_id)
);
```

#### `metrics` Table
```sql
CREATE TABLE metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metadata TEXT
);
```

#### `observability_events` Table
```sql
CREATE TABLE observability_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT,
    duration_ms REAL
);
```

### Session Database: `adk_sessions.db`

Managed by ADK's DatabaseSessionService. Stores serialized session state including conversation history and agent outputs.

---

## API Endpoints

### `GET /`
**Purpose**: Render main web interface

**Response**: HTML page (Jinja2 template)

---

### `POST /api/analyze`
**Purpose**: Analyze user input for scams

**Request Body**:
```json
{
  "session_id": "uuid-string",
  "user_input": "Text or URL to analyze",
  "input_type": "text|url|image|mixed"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "report": "Analysis report text",
    "risk_level": "HIGH|MEDIUM|LOW|UNCLEAR",
    "session_id": "uuid-string",
    "check_id": 123
  }
}
```

---

### `POST /api/feedback`
**Purpose**: Submit user feedback on analysis

**Request Body**:
```json
{
  "check_id": 123,
  "rating": 5,
  "helpful": true,
  "comments": "Optional feedback text"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Feedback recorded"
}
```

---

### `GET /api/health`
**Purpose**: Health check endpoint

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-29T12:00:00",
  "database": "connected",
  "session_service": "active"
}
```

---

### `GET /observability`
**Purpose**: Observability dashboard

**Response**: HTML dashboard with:
- System health status
- Agent performance metrics
- Recent error log
- Auto-refresh every 30 seconds

---

## External Integrations

### Google Safe Browsing API
**Purpose**: Check URLs against Google's threat databases

**Endpoint**: `https://safebrowsing.googleapis.com/v4/threatMatches:find`

**Authentication**: API key via `SAFE_BROWSING_API_KEY` environment variable

**Detects**:
- Phishing sites
- Malware distribution
- Unwanted software
- Social engineering

---

### URLhaus API
**Purpose**: Check URLs against malware database

**Endpoint**: `https://urlhaus-api.abuse.ch/v1/url/`

**Authentication**: None (public API)

**Detects**:
- Malware distribution URLs
- Command & control servers
- Known malicious domains

---

### Google Search (ADK Tool)
**Purpose**: Find location-specific scam reporting contacts

**Implementation**: `google.adk.tools.google_search`

**Used by**: ResourceAssistantAgent

---

## Session Management

### Development: InMemorySessionService
- Fast, ephemeral storage
- Lost on server restart
- Good for testing and debugging

### Production: DatabaseSessionService
- Persistent storage in SQLite/PostgreSQL
- Survives server restarts
- Enables multi-server deployments
- Stores conversation history and agent outputs

### Configuration
Set via environment variable:
```bash
USE_DATABASE_SESSIONS=True  # DatabaseSessionService
USE_DATABASE_SESSIONS=False # InMemorySessionService
```

---

## Observability

### Logging Strategy

#### Application Logs (`observability.log`)
- **Level**: INFO (production), DEBUG (development)
- **Rotation**: 10MB max, 5 backup files
- **Content**: Workflow steps, errors, warnings

#### Debug Logs (`adk_debug.log`)
- **Level**: DEBUG
- **Content**: Full LLM requests/responses, system instructions, function calls
- **Activation**: Set `LOG_LEVEL=DEBUG` in `.env`

### Event Tracking
- Agent invocations
- Tool calls
- Errors and exceptions
- Performance metrics (duration, success rate)

### Dashboard
- Real-time system health
- Agent performance graphs
- Recent errors
- Database statistics

### CLI Management
```bash
python db_cli.py --logs        # List log files
python db_cli.py --tail        # View recent logs
python db_cli.py --clean-logs  # Archive old logs
```

---

## Deployment

### Development Setup
```bash
# Environment variables
LOG_LEVEL=DEBUG
USE_DATABASE_SESSIONS=False
FLASK_USE_RELOADER=False

# Run
python back_end/app.py
```

### Production Recommendations

#### Environment
```bash
LOG_LEVEL=INFO
USE_DATABASE_SESSIONS=True
FLASK_USE_RELOADER=False
```

#### Web Server
Use production WSGI server (Gunicorn, uWSGI):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 back_end.app:app
```

#### Database
Migrate to PostgreSQL for production:
```python
# Update session_config.py
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://...')
```

#### Security
- Enable HTTPS
- Set strong `SECRET_KEY` for Flask sessions
- Restrict CORS origins
- Rate limiting on API endpoints
- Input validation and sanitization

#### Monitoring
- Set up log aggregation (ELK, Splunk)
- Configure alerts for error rates
- Monitor database performance
- Track API response times

---

## Performance Considerations

### Response Time Targets
- **Text Analysis**: < 3 seconds
- **URL Analysis**: < 2 seconds (cached) / < 5 seconds (fresh)
- **Full Report**: < 8 seconds

### Optimization Strategies
1. **Caching**: Cache URLhaus and Safe Browsing results (1 hour TTL)
2. **Parallel Processing**: Run TextAnalyzer and URLAnalyzer concurrently
3. **Database Indexing**: Index session_id, timestamp columns
4. **Log Rotation**: Prevent disk space issues
5. **Session Cleanup**: Purge old sessions (> 30 days)

---

## Security Architecture

### Input Validation
- Sanitize user input before processing
- Validate URLs before querying
- Limit input size (10KB max)

### API Security
- Rate limiting (100 requests/hour per IP)
- CSRF protection on forms
- Content Security Policy headers

### Data Privacy
- No PII storage (optional location/role only)
- Session data encrypted at rest
- Automatic session expiration

### Dependency Security
- Regular `pip audit` checks
- Pinned package versions in requirements.txt
- Automated CVE scanning

---

**Last Updated**: November 29, 2025  
**Version**: 1.0  
**Maintained by**: Scam Detection Tool Team
