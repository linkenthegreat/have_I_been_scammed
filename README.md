# Scam Prevention Tool 🛡️

This project is inspirec by Have I Been Pwned (https://haveibeenpwned.com/).
An open-source AI-powered web application to help the public detect and avoid fraud and scams. Built with **Google ADK** and **Gemini 2.5 Flash** for the "5-Day AI Agents Intensive Course with Google" capstone project.

## 🚀 Features
- **5-Agent System**: Orchestrator coordinates Receptionist, Text Analyzer, URL Analyzer, Report Generator, and Resource Assistant using ADK's LLM-Orchestrated pattern
- **5 Integrated Tools**: Google Search (ADK built-in), Safe Browsing API, URLhaus malware database, URL metadata analysis, database session tools
- **Proper ADK Architecture**: Sub-agents wrapped as AgentTools, single Runner, automatic LLM coordination
- **Multi-Input Support**: Analyzes text messages, URLs, images, and mixed content
- **Global Reporting**: Finds location-specific scam reporting contacts (Australia, US, UK, etc.)
- **User Context Gathering**: Optional location and role collection for personalized help
- **Long-Term Memory**: SQLite database tracks sessions, analysis history, and user feedback
- **Enhanced Observability**: DEBUG-level logging with ADK built-in observability, rotating log files, CLI management tools
- **Session Persistence**: Database-backed sessions survive server restarts
- **Production-Ready**: Stable configuration, comprehensive logging, health check endpoints

## 🛠️ Tech Stack
- **Backend**: Python, Flask
- **AI Framework**: Google ADK (Agent Development Kit)
- **AI Model**: Gemini 2.5 Flash (multimodal, multilingual)
- **Database**: SQLite (Dev) → PostgreSQL (Prod-ready)
- **Frontend**: Vanilla HTML/CSS/JavaScript with Jinja2
- **Testing**: pytest with TDD approach

## 📂 Project Structure
- `agents_n_tools/`: 5 ADK agents (Orchestrator, Receptionist, Text Analyzer, URL Analyzer, Report Generator, Resource Assistant) + custom tools (Safe Browsing, URLhaus, URL metadata)
- `back_end/`: Flask API, orchestrator service, observability tracking, session management
- `front_end/`: Web interface with collapsible context gathering
- `data/`: SQLite database with 5 tables (sessions, scam_checks, feedback, metrics, observability_events)
- `docs/`: Architecture docs and guides
- `tests/`: Unit tests (7/7 passing)
- `adk_notebook/`: ADK learning notebooks and observability documentation
- `logs/`: Application and debug logs (rotating files)
- `db_cli.py`: Database and log management CLI tool

## 🚦 Getting Started

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone [repo-url]
   cd have_I_been_scammed
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python check_dependencies.py
   ```
   This will check all required packages and their versions.

4. **Set up environment**
   - Copy `.env.example` to `.env`
   - Add required API keys:
     ```bash
     GOOGLE_API_KEY=your_api_key_here  # Required
     SAFE_BROWSING_API_KEY=your_key    # Optional but recommended
     ```
   - Configure settings (optional):
     ```bash
     LOG_LEVEL=DEBUG                   # DEBUG for development, INFO for production
     USE_DATABASE_SESSIONS=True        # Enable persistent sessions
     FLASK_USE_RELOADER=False          # Disable auto-reload (recommended)
     ```

5. **Run the application**
   ```bash
   python back_end/app.py
   ```

6. **Access the application**
   - Main interface: `http://localhost:5000`
   - Observability dashboard: `http://localhost:5000/observability`
   - Health check: `http://localhost:5000/api/health`

7. **Manage logs** (optional)
   ```bash
   python db_cli.py --help  # See all log management commands
   python db_cli.py --logs   # List log files
   python db_cli.py --tail   # View recent logs
   ```

### Quick Install (One-liner)
```bash
git clone [repo-url] && cd have_I_been_scammed && pip install -r requirements.txt && python check_dependencies.py
```

## 🎯 Kaggle Requirements Met 
✅ Multi-agent system (5 specialized agents + orchestrator)  
✅ Tools integration (5 tools)  
✅ Sessions & memory (SQLite + Flask sessions with database persistence)  
✅ Observability (metrics table + event tracking + DEBUG logging + dashboard)  
✅ Agent evaluation (user feedback system)

## 🛠️ Developer Tools

### Database CLI (`db_cli.py`)
Comprehensive CLI for database inspection and log management:

**Database Operations:**
- `python db_cli.py --tables` - List all tables
- `python db_cli.py --sessions` - Show recent sessions
- `python db_cli.py --checks` - Show recent scam checks
- `python db_cli.py --stats` - Database statistics
- `python db_cli.py --verify` - Verify database integrity

**Log Management:**
- `python db_cli.py --logs` - List all log files with sizes
- `python db_cli.py --tail` - View last 50 lines of observability.log
- `python db_cli.py --tail --file adk_debug.log --lines 100` - Custom log tail
- `python db_cli.py --clean-logs` - Clean logs (with backup)
- `python db_cli.py --delete-backups` - Delete .bak backup files

### Observability Dashboard
Access `http://localhost:5000/observability` for:
- Real-time system health status
- Agent and tool performance metrics
- Recent error tracking
- Auto-refresh every 30 seconds

## 📊 Development Status

### Completed Phases
- ✅ **Phase 0**: Core 5-agent system with multimodal support
- ✅ **Phase 1.1**: Fixed Flask watchdog configuration
- ✅ **Phase 1.2**: Implemented DatabaseSessionService for persistence
- ✅ **Phase 3**: Observability system with event tracking and dashboard
- ✅ **Phase 4**: Export functions and email drafting
- ✅ **Phase 4.5**: Enhanced observability with ADK DEBUG logging
- ✅ **Phase 5**: Documentation updates and production readiness (COMPLETED)

### System Status
✅ **Production Ready** - All core features implemented, documented, and tested

See `development_idea/system_v1_improve_plan.md` for detailed roadmap and `docs/PHASE_5_COMPLETION.md` for latest completion report.

## 🤝 Contributing
This is a capstone project. See `docs/` for architecture details.

## 📚 Documentation

### Quick Links
- **Getting Started**: See installation steps above
- **Architecture**: `docs/architecture.md` - Complete system design and diagrams
- **Glossary**: `docs/glossary.md` - Scam terminology and technical definitions
- **Database CLI Guide**: `docs/DB_CLI_GUIDE.md` - Developer tools reference
- **Troubleshooting**: `docs/INSTALLATION_TROUBLESHOOTING.md` - Common issues and solutions
- **Phase 5 Report**: `docs/PHASE_5_COMPLETION.md` - Latest completion summary
- **ADK Observability**: `adk_notebook/observability_google_adk.md` - Logging and monitoring guide

### Component Documentation
- **Backend**: `back_end/README.md` - API endpoints and services
- **Agents**: `agents_n_tools/README.md` - Agent architecture and workflows
- **Database**: `data/README.md` - Schema and data management
- **Tests**: `tests/README.md` - Testing strategy and coverage

---

**Built for**: Google's 5-Day AI Agents Intensive Course Capstone Project  
**Status**: ✅ Production Ready  
**Last Updated**: November 29, 2025 