# Agents & Tools 🕵️‍♂️

This directory contains the AI agents powered by **Google ADK** (Agent Development Kit) and Gemini 2.5 Flash.

## Agent Architecture (7-Agent System)

We use an **LLM-Orchestrated Multi-Agent System** with 7 specialized agents:

### Agent Hierarchy

```
OrchestratorAgent (Root)
├── ReceptionistAgent          # User interaction & context gathering
├── TextAnalyzerAgent          # Text/image scam pattern detection
├── URLAnalyzerAgent           # URL safety analysis (with 3 tools)
├── ReportGeneratorAgent       # Compile findings into user report
├── ResourceAssistantAgent     # Find local reporting contacts
└── RecordKeeperAgent          # Talk to Database (Legacy from previous version. Not in use)
```

### Agent Descriptions

1. **OrchestratorAgent** (Root)
   - **Role**: Routes requests to appropriate specialist agents
   - **Pattern**: LLM-Orchestrated (dynamic decision-making)
   - **Sub-agents**: All 6 specialists wrapped as `AgentTool`

2. **ReceptionistAgent**
   - **Role**: Handles user interaction, gathers context (location, role)
   - **Tools**: `update_session_context`, `get_session_context`
   - **Output Key**: N/A (conversational agent)

3. **TextAnalyzerAgent**
   - **Role**: Analyzes text and screenshots for scam patterns
   - **Tools**: None (uses LLM multimodal capabilities)
   - **Output Key**: `text_analysis_result`
   - **Detects**: Urgency tactics, threats, suspicious requests, grammar errors

4. **URLAnalyzerAgent**
   - **Role**: Checks URLs against safety databases
   - **Tools**: `check_url_safety`, `check_urlhaus`, `extract_url_metadata`
   - **Output Key**: `url_analysis_result`
   - **Analyzes**: Safe Browsing database, malware databases, domain characteristics

5. **ReportGeneratorAgent**
   - **Role**: Compiles specialist findings into a clear, actionable report
   - **Input Keys**: `text_analysis_result`, `url_analysis_result`
   - **Output Key**: `final_report`
   - **Format**: Risk assessment, reasoning, actionable steps, resources

6. **ResourceAssistantAgent**
   - **Role**: Finds location-specific scam reporting contacts
   - **Tools**: `google_search` (ADK built-in)
   - **Context-aware**: Uses `user:location` from session state

7. **RecordKeeperAgent**
   - **Role**: Logs analysis to database for long-term memory
   - **Tools**: `log_scam_check`, `get_recent_checks`
   - **Storage**: Session state (short-term) + SQLite (long-term)

---

## Tools Integration

### External API Tools
- **`check_url_safety`** - Google Safe Browsing API (malicious URL detection)
- **`check_urlhaus`** - URLhaus API (malware/botnet database)
- **`extract_url_metadata`** - Domain analysis (SSL, TLD, IP-based URLs)

### Built-in ADK Tools
- **`google_search`** - Real-time web search (used by ResourceAssistantAgent)

### Session State Tools (ToolContext-enabled)
- **`log_scam_check`** - Logs analysis to session state + database
- **`get_recent_checks`** - Retrieves past analyses from session
- **`update_session_context`** - Stores user location/role
- **`get_session_context`** - Retrieves user context

All session state tools use `ToolContext` for automatic session management.

---

## Subdirectories

### `agent_prompts/`
YAML configuration files defining each agent's:
- `name`: Agent identifier
- `model`: Gemini model version (e.g., `gemini-2.5-flash`)
- `description`: Brief agent purpose
- `instruction`: Detailed behavioral instructions (uses YAML multiline format)
- `output_key`: State key for multi-agent coordination (optional)

**Format**: YAML (migrated from JSON in Phase 2 for better readability)

**Files:**
- `orchestrator_agent.yaml` - Root orchestrator configuration
- `receptionist_agent.yaml` - User interaction agent
- `text_analyzer_agent.yaml` - Text scam detection agent
- `url_analyzer_agent.yaml` - URL safety analysis agent
- `report_generator_agent.yaml` - Report compilation agent
- `resource_assistant_agent.yaml` - Resource finder agent
- `record_keeper_agent.yaml` - Database logging agent

### `tools/`
Python implementations of custom tools following ADK best practices:
- **Return dictionaries** with `status` field
- **Include docstrings** (LLM-readable)
- **Use type hints** for all parameters
- **Use `ToolContext`** for session state access
- **Handle errors gracefully** (no exceptions)

**Files:**
- `safe_browsing.py` - Google Safe Browsing API integration
- `urlhaus_checker.py` - URLhaus malware database checker
- `url_metadata.py` - Domain metadata extraction
- `db_tools.py` - Session state + database tools

---

## Core Module: `agent.py`

### Functions

#### `load_agent_config(agent_name: str) -> dict`
Loads YAML or JSON configuration for a specific agent.
- **Args**: `agent_name` (e.g., "text_analyzer_agent")
- **Returns**: Dictionary with agent configuration
- **Behavior**: Tries `.yaml` first (preferred), falls back to `.json` for backward compatibility
- **Raises**: `FileNotFoundError` if neither config exists

#### `create_retry_config() -> types.HttpRetryOptions`
Creates retry configuration for handling API rate limits and transient errors.
- **Returns**: Retry options (5 attempts, exponential backoff)
- **HTTP codes**: 429, 500, 503, 504

### Classes

#### `AgentFactory`
Factory class for creating ADK LlmAgent instances.

**Methods:**
- **`create_agent(agent_name: str, tools: list = None) -> LlmAgent`**
  - Loads YAML config (preferred) or JSON config (fallback)
  - Creates `Gemini` model with retry configuration
  - Instantiates `LlmAgent` with proper ADK parameters
  - **Args**: 
    - `agent_name`: Config file name (without extension)
    - `tools`: Optional list of tool functions
  - **Returns**: Configured `LlmAgent` instance

### Helper Functions

Convenience functions to get specific pre-configured agents:
- `get_orchestrator_agent() -> LlmAgent`
- `get_receptionist_agent() -> LlmAgent`
- `get_text_analyzer_agent() -> LlmAgent`
- `get_url_analyzer_agent() -> LlmAgent` (includes 3 URL safety tools)
- `get_report_generator_agent() -> LlmAgent`
- `get_resource_assistant_agent() -> LlmAgent` (includes google_search)
- `get_record_keeper_agent(tools: list = None) -> LlmAgent`

---

## ADK Integration Details

### Agent Type: `LlmAgent`
We use `LlmAgent` (not base `Agent`) because our agents:
- Use LLM reasoning (Gemini)
- Execute tools
- Follow text instructions
- Share state via `output_key`

### Model Configuration
```python
model = Gemini(
    model="gemini-2.5-flash",
    retry_options=create_retry_config()  # Automatic retry on failures
)
```

### Multi-Agent State Sharing
Agents use `output_key` to share results:
```python
text_analyzer = LlmAgent(
    name="TextAnalyzerAgent",
    output_key="text_analysis_result"  # Other agents can read this
)

report_generator = LlmAgent(
    name="ReportGeneratorAgent",
    instruction="Create report from: {text_analysis_result}"  # Reads previous result
)
```

### Tool Context Pattern
Database tools use `ToolContext` for automatic session management:
```python
def log_scam_check(tool_context: ToolContext, input_type: str, ...) -> dict:
    session_id = tool_context.session_id  # Auto-injected by ADK
    tool_context.state["check:timestamp"] = data  # Session state storage
```

---

## Requirements

### Python Packages
```
google-adk>=0.1.0
python-dotenv>=1.0.0
requests>=2.31.0
```

### Environment Variables
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
SAFE_BROWSING_API_KEY=your_safe_browsing_key_here  # Optional
```

### External APIs
- **Google Gemini API** - Required (get key at https://aistudio.google.com/app/api-keys)
- **Google Safe Browsing API** - Optional (enhances URL safety checks)
- **URLhaus API** - Required (get key at https://urlhaus.abuse.ch/api/)

---

## Usage Example

```python
from agents_n_tools.agent import (
    get_orchestrator_agent,
    get_text_analyzer_agent,
    get_url_analyzer_agent
)
from google.adk.runners import InMemoryRunner

# Create orchestrator
orchestrator = get_orchestrator_agent()

# Run with simple runner (for testing)
runner = InMemoryRunner(agent=orchestrator)
response = await runner.run_debug("Check this URL: http://suspicious-site.com")

# For production, use Runner with SessionService and MemoryService
```

---

## Testing

See `agents_test_plan.md` for comprehensive testing strategy.

**Quick Test:**
```bash
cd agents_n_tools
python -m pytest tests/ -v
```

---

## References

- **ADK Documentation**: https://google.github.io/adk-docs/
- **ADK Agents Guide**: https://google.github.io/adk-docs/agents/
- **ADK Tools Guide**: https://google.github.io/adk-docs/tools/
- **ADK Runtime Guide**: https://google.github.io/adk-docs/runtime/
- **Gemini API Docs**: https://ai.google.dev/gemini-api/docs
- **Gemini Pricing**: https://ai.google.dev/gemini-api/docs/pricing
- **Safe Browsing API**: https://developers.google.com/safe-browsing/v4
- **URLhaus API**: https://urlhaus-api.abuse.ch/

---

## Architecture Decisions

### Why LLM-Orchestrated Pattern?
- ✅ **Flexibility**: Orchestrator adapts to user input dynamically
- ✅ **Modularity**: Easy to add/remove specialist agents
- ✅ **Testability**: Each agent can be tested independently
- ✅ **Scalability**: Agents can be deployed as separate services later

### Why Not Sequential/Parallel?
- ❌ **Sequential**: Too rigid (can't skip unnecessary steps)
- ❌ **Parallel**: Wastes resources (not all agents needed for every request)
- ✅ **LLM-Orchestrated**: Only calls agents when needed

### Why Session State + Database?
- **Session State**: Fast, temporary storage for active conversations
- **Database**: Persistent storage for analytics, feedback, long-term memory
- **Best of Both**: Performance + persistence

---

## Future Enhancements

1. **Memory Service Integration**: Migrate to ADK's `MemoryService` for semantic search across past analyses
2. **Agent2Agent Protocol**: Expose agents as microservices using A2A
3. **Custom MCP Tools**: Add more external tool integrations (VirusTotal, PhishTank)
4. **Evaluation Framework**: Automated testing with ADK's evaluation tools

---

*Last Updated: 2025-11-27*
*ADK Version: 0.1.0+*
*Model: gemini-2.5-flash*