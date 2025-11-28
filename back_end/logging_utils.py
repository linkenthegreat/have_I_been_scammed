"""
Enhanced logging utilities for LLM debugging.
Captures detailed request/response data for troubleshooting.

Part of Phase 4.5: Enhanced Observability
"""
import logging
import json
from typing import Any, Dict

logger = logging.getLogger(__name__)


def log_llm_request(agent_name: str, request_data: Dict[str, Any]):
    """
    Log detailed LLM request for debugging.
    
    Captures:
    - System instructions
    - Conversation history
    - Available tools/functions
    - Model parameters
    
    Args:
        agent_name: Name of the agent making the request
        request_data: Dictionary containing system_instruction, contents, tools
    """
    logger.debug("=" * 60)
    logger.debug(f"LLM Request from {agent_name}")
    logger.debug("=" * 60)
    
    if 'system_instruction' in request_data:
        logger.debug("System Instruction:")
        logger.debug(f"  {request_data['system_instruction']}")
    
    if 'contents' in request_data:
        logger.debug("Contents:")
        for i, content in enumerate(request_data['contents']):
            logger.debug(f"  [{i}] {json.dumps(content, indent=4)}")
    
    if 'tools' in request_data and request_data['tools']:
        logger.debug("Functions:")
        for tool in request_data['tools']:
            logger.debug(f"  {tool.get('name')}: {tool.get('parameters')}")
    
    logger.debug("=" * 60)


def log_llm_response(agent_name: str, response_data: Dict[str, Any]):
    """
    Log detailed LLM response for debugging.
    
    Captures:
    - Response text
    - Function calls made
    - Error messages
    - Token usage
    
    Args:
        agent_name: Name of the agent receiving the response
        response_data: Dictionary containing text, function_calls, usage, error
    """
    logger.debug("=" * 60)
    logger.debug(f"LLM Response to {agent_name}")
    logger.debug("=" * 60)
    
    if 'text' in response_data and response_data['text']:
        logger.debug("Text:")
        logger.debug(f"  {response_data['text']}")
    
    if 'function_calls' in response_data and response_data['function_calls']:
        logger.debug("Function Calls:")
        for fc in response_data['function_calls']:
            logger.debug(f"  {fc.get('name')}({json.dumps(fc.get('args'), indent=4)})")
    
    if 'error' in response_data:
        logger.error(f"ERROR: {response_data['error']}")
    
    if 'usage' in response_data and response_data['usage']:
        logger.debug(f"Token Usage: {response_data['usage']}")
    
    logger.debug("=" * 60)


def log_tool_call(tool_name: str, args: Dict[str, Any], result: Any):
    """
    Log tool invocation with parameters and result.
    
    Args:
        tool_name: Name of the tool being called
        args: Tool arguments as dictionary
        result: Tool execution result
    """
    logger.debug(f"🔧 Tool Call: {tool_name}")
    logger.debug(f"   Args: {json.dumps(args, indent=4)}")
    
    # Handle result formatting
    if isinstance(result, dict):
        result_str = json.dumps(result, indent=4)
    elif isinstance(result, str):
        result_str = result
    else:
        result_str = str(result)
    
    logger.debug(f"   Result: {result_str}")


def sanitize_log(text: str) -> str:
    """
    Remove sensitive data from logs (emails, phone numbers, API keys).
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text with sensitive data replaced
    """
    import re
    
    if not text:
        return text
    
    # Remove emails
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL_REDACTED]',
        text
    )
    
    # Remove phone numbers (various formats)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]', text)
    text = re.sub(r'\+\d{1,3}[-.]?\d{1,14}\b', '[PHONE_REDACTED]', text)
    
    # Remove API keys (Gemini format)
    text = re.sub(r'AIza[0-9A-Za-z_-]{35}', '[API_KEY_REDACTED]', text)
    
    # Remove credit card numbers
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_REDACTED]', text)
    
    return text
