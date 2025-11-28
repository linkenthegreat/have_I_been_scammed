import json
import yaml
import os
from pathlib import Path
from google.adk.agents import LlmAgent  # Not Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "agent_prompts"

def load_agent_config(agent_name):
    """Loads the YAML or JSON configuration for a specific agent.
    
    Tries to load .yaml first (preferred), falls back to .json for backward compatibility.
    """
    yaml_path = PROMPTS_DIR / f"{agent_name}.yaml"
    json_path = PROMPTS_DIR / f"{agent_name}.json"
    
    # Try YAML first (preferred format)
    if yaml_path.exists():
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    # Fallback to JSON for backward compatibility
    elif json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    else:
        raise FileNotFoundError(f"Agent config not found: {agent_name} (tried .yaml and .json)")

def create_retry_config():
    """Creates retry configuration for handling API errors."""
    return types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504]
    )

class AgentFactory:
    """Factory class to create ADK agents based on config."""
    
    @staticmethod
    def create_agent(agent_name, tools=None, sub_agents=None):
        """
        Creates a configured ADK LlmAgent instance.
        
        Args:
            agent_name (str): Name of the agent config file (e.g., 'text_analyzer_agent').
            tools (list): Optional list of tool functions to bind to the agent.
            sub_agents (list): Optional list of sub-agents to bind to the agent.
            
        Returns:
            LlmAgent: The configured ADK Agent.
        """
        config = load_agent_config(agent_name)
        
        # Create LlmAgent with proper ADK parameters
        agent = LlmAgent(
            name=config.get("name", agent_name),
            model=Gemini(
                model=config.get("model", "gemini-2.5-flash"),
                retry_options=create_retry_config()  # Enable automatic retry on errors
            ),
            description=config.get("description", ""),
            instruction=config.get("instruction", ""),
            tools=tools if tools else [],
            sub_agents=sub_agents if sub_agents else [],
            output_key=config.get("output_key")  # Support output_key for state sharing
        )
        
        return agent

# Helper functions to get specific agents (non-orchestrator)
def get_text_analyzer_agent():
    """Creates Text Analyzer agent (no tools needed, uses LLM multimodal)."""
    return AgentFactory.create_agent("text_analyzer_agent")

def get_url_analyzer_agent():
    """Creates URL Analyzer with all safety checking tools."""
    from agents_n_tools.tools import safe_browsing, urlhaus_checker, url_metadata
    return AgentFactory.create_agent(
        "url_analyzer_agent", 
        tools=[
            safe_browsing.check_url_safety,
            urlhaus_checker.check_urlhaus,
            url_metadata.extract_url_metadata
        ]
    )

def get_receptionist_agent():
    """Creates Receptionist agent for user interaction."""
    return AgentFactory.create_agent("receptionist_agent")

def get_report_generator_agent():
    """Creates Report Generator agent."""
    return AgentFactory.create_agent("report_generator_agent")

def get_resource_assistant_agent():
    """Creates Resource Assistant with Google Search enabled."""
    from google.adk.tools import google_search  # ← Use built-in ADK tool
    return AgentFactory.create_agent(
        "resource_assistant_agent", 
        tools=[google_search]
    )

# RecordKeeperAgent removed - backend handles all logging automatically
# def get_record_keeper_agent():
#     """Creates Record Keeper with database logging tools."""
#     from agents_n_tools.tools.db_tools import log_scam_check
#     return AgentFactory.create_agent(
#         "record_keeper_agent", 
#         tools=[log_scam_check]
#     )

def get_orchestrator_agent():
    """
    Creates the root orchestrator agent with all specialists as tools.
    This implements the LLM-Orchestrated Multi-Agent pattern.
    """
    from google.adk.tools import AgentTool
    
    # Create all specialist agents
    text_analyzer = get_text_analyzer_agent()
    url_analyzer = get_url_analyzer_agent()
    receptionist = get_receptionist_agent()
    report_generator = get_report_generator_agent()
    resource_assistant = get_resource_assistant_agent()
    # RecordKeeperAgent removed - backend handles all logging automatically
    
    # Wrap specialists as AgentTools
    # The LLM will decide when to call each specialist
    specialist_tools = [
        AgentTool(agent=receptionist),
        AgentTool(agent=text_analyzer),
        AgentTool(agent=url_analyzer),
        AgentTool(agent=report_generator),
        AgentTool(agent=resource_assistant)
        # RecordKeeperAgent not included - logging handled by backend
    ]
    
    # Pass AgentTools to the tools parameter, not sub_agents
    return AgentFactory.create_agent(
        "orchestrator_agent",
        tools=specialist_tools  # LLM orchestrates these via tools
    )

