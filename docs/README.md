# Documentation 📚

Detailed project documentation and guides.

## Files

### Architecture & Design
- `architecture.md`: Complete system design, component diagrams, and data flow
- `glossary.md`: Definitions of scam-related terms and technical concepts

### Guides & Tutorials
- `INSTALLATION_TROUBLESHOOTING.md`: Common installation issues and solutions
- `DB_CLI_GUIDE.md`: Database and log management CLI quick reference
- `PHASE_5_COMPLETION.md`: Phase 5 documentation completion report

### Legacy Documentation
- `ARCHITECTURE_REFACTOR.md`: Historical ADK compliance refactor documentation
- `setup.md`: Legacy setup guide (superseded by main README.md)

## Additional Documentation

### Component Documentation
- **Backend**: `../back_end/README.md` - API endpoints and services
- **Agents**: `../agents_n_tools/README.md` - 5-agent architecture and workflows
- **Database**: `../data/README.md` - Schema and data management
- **Frontend**: `../front_end/README.md` - UI components
- **Tests**: `../tests/README.md` - Testing strategy

### Developer Tools
- `db_cli.py --help`: Database and log management CLI reference
- `check_dependencies.py`: Automated dependency verification

### ADK Notebooks (`../adk_notebook/`)
- `observability_google_adk.md`: Comprehensive guide to ADK observability and logging
- `google_adk_basic.md`: ADK fundamentals
- `day-*.ipynb`: Learning notebooks from 5-day intensive course

## Key Concepts

### Agent Architecture
- **LLM-Orchestrated Pattern**: Root orchestrator with 5 specialist agents as AgentTools
- **Single Runner**: One ADK Runner manages all agent coordination
- **State Sharing**: Agents communicate via `output_key` and session state
- **Tool Context**: Automatic session injection for database tools

### 5-Agent System
1. **OrchestratorAgent**: Root coordinator with LLM-based routing
2. **ReceptionistAgent**: User interaction & context gathering
3. **TextAnalyzerAgent**: Text/image scam pattern detection
4. **URLAnalyzerAgent**: URL safety analysis (with 3 external tools)
5. **ReportGeneratorAgent**: Compile findings into actionable reports
6. **ResourceAssistantAgent**: Find location-specific reporting contacts

**Note**: RecordKeeperAgent removed - backend handles all logging automatically

### Session Management
- **DatabaseSessionService**: Persistent sessions survive server restarts
- **InMemorySessionService**: Testing mode for ephemeral sessions
- **Context Preservation**: User location, role, and conversation history maintained

### Observability
- **Event Tracking**: All agent calls, tool invocations, and errors logged
- **Performance Metrics**: Duration tracking for agents and tools
- **Dashboard**: Real-time monitoring at `/observability` endpoint
- **DEBUG Logging**: ADK built-in logging provides full LLM request/response visibility

## Getting Started
1. Read `setup.md` for installation instructions
2. Review `ARCHITECTURE_REFACTOR.md` for system design
3. Explore `../adk_notebook/observability_google_adk.md` for debugging guide
4. Check `../development_idea/system_v1_improve_plan.md` for roadmap

## Requirements
- None (Markdown files)

## References
- Project Main README: `../README.md`
- Google ADK Documentation: https://google.github.io/adk-docs/
- Flask Documentation: https://flask.palletsprojects.com/
- URLhaus: https://urlhaus.abuse.ch/api/
- Google Safe Browsing: https://developers.google.com/safe-browsing
- Have I Been Pwned: https://haveibeenpwned.com/