# Documentation 📚

Detailed project documentation and guides.

## Files
- `ARCHITECTURE_REFACTOR.md`: ADK compliance refactor and multi-agent architecture
- `INSTALLATION_TROUBLESHOOTING.md`: Common installation issues and solutions
- `PHASE_5_COMPLETION.md`: Phase 5 documentation update completion report
- `DB_CLI_GUIDE.md`: Database and log management CLI quick reference
- `setup.md`: Step-by-step installation guide
- `glossary.md`: Definitions of scam-related terms
- `architecture.md`: System design and diagrams

## Additional Documentation

### ADK Notebooks (`../adk_notebook/`)
- `observability_google_adk.md`: Comprehensive guide to ADK observability and logging
- `day-*.ipynb`: ADK learning notebooks from 5-day intensive course

### Development Planning (`../development_idea/`)
- `system_v1_improve_plan.md`: Complete development roadmap with phase tracking
- `agent_schema_draft_v1.csv`: Agent specifications and workflows

### Tool Documentation
- `db_cli.py --help`: Database and log management CLI reference
- Back-end API: `../back_end/README.md`
- Agent System: `../agents_n_tools/README.md`
- Data Schema: `../data/README.md`

## Key Concepts

### Agent Architecture
- **LLM-Orchestrated Pattern**: Root orchestrator with 6 sub-agents as AgentTools
- **Single Runner**: One ADK Runner manages all agent coordination
- **State Sharing**: Agents communicate via `output_key` and session state
- **Tool Context**: Automatic session injection for database tools

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
