"""
Custom ADK Plugin for detailed request/response logging.
Goes beyond standard LoggingPlugin to capture LLM internals.

Part of Phase 4.5: Enhanced Observability
"""
import logging
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.callback_context import CallbackContext
from back_end.logging_utils import log_llm_request, log_llm_response, log_tool_call

logger = logging.getLogger(__name__)


class DetailedLoggingPlugin(BasePlugin):
    """
    Enhanced logging plugin that captures:
    - Full LLM requests (system instructions, history, tools)
    - Complete LLM responses (text, function calls, errors)
    - Tool execution details (parameters, results, timing)
    """
    
    def __init__(self):
        super().__init__(name="detailed_logging")
        self.request_count = 0
        self.tool_call_count = 0
        logger.info("DetailedLoggingPlugin initialized")
    
    async def before_model_callback(
        self, 
        *, 
        callback_context: CallbackContext, 
        llm_request
    ) -> None:
        """Log full LLM request before sending to model."""
        self.request_count += 1
        
        # Get agent name from callback context (may not always be available)
        agent_name = "Unknown"
        if hasattr(callback_context, 'agent') and callback_context.agent:
            agent_name = callback_context.agent.name
        
        logger.info(f">> LLM Request #{self.request_count} from {agent_name}")
        
        try:
            # Extract request details - use defensive attribute access
            request_data = {}
            
            # Try different possible attribute names for system instruction
            if hasattr(llm_request, 'system_instruction'):
                request_data['system_instruction'] = llm_request.system_instruction
            elif hasattr(llm_request, 'system_prompt'):
                request_data['system_instruction'] = llm_request.system_prompt
            
            # Try to get contents
            if hasattr(llm_request, 'contents'):
                request_data['contents'] = [self._format_content(c) for c in llm_request.contents]
            
            # Try to get tools
            if hasattr(llm_request, 'tools') and llm_request.tools:
                request_data['tools'] = [self._format_tool(t) for t in llm_request.tools]
            
            log_llm_request(agent_name, request_data)
        except Exception as e:
            logger.error(f"Error logging LLM request: {e}", exc_info=True)
    
    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_response,
        **kwargs  # Accept any additional parameters ADK might pass
    ) -> None:
        """Log full LLM response after receiving from model."""
        # Get agent name from callback context (may not always be available)
        agent_name = "Unknown"
        if hasattr(callback_context, 'agent') and callback_context.agent:
            agent_name = callback_context.agent.name
        
        logger.info(f"<< LLM Response to {agent_name}")
        
        try:
            # Extract response details
            response_data = {
                'text': llm_response.text if hasattr(llm_response, 'text') else None,
                'function_calls': self._extract_function_calls(llm_response),
                'usage': self._extract_usage(llm_response)
            }
            
            log_llm_response(agent_name, response_data)
        except Exception as e:
            logger.error(f"Error logging LLM response: {e}", exc_info=True)
    
    async def before_tool_callback(
        self,
        *,
        callback_context: CallbackContext,
        tool_name: str,
        tool_args: dict
    ) -> None:
        """Log tool invocation before execution."""
        self.tool_call_count += 1
        logger.info(f"[TOOL] Call #{self.tool_call_count}: {tool_name}")
        logger.debug(f"   Parameters: {tool_args}")
    
    async def after_tool_callback(
        self,
        *,
        callback_context: CallbackContext,
        tool_name: str,
        tool_args: dict,
        tool_result: any
    ) -> None:
        """Log tool result after execution."""
        logger.info(f"[TOOL] Result: {tool_name}")
        
        try:
            log_tool_call(tool_name, tool_args, tool_result)
        except Exception as e:
            logger.error(f"Error logging tool result: {e}", exc_info=True)
    
    async def on_model_error_callback(
        self,
        *,
        callback_context: CallbackContext,
        error: Exception,
        **kwargs  # Accept any additional parameters ADK might pass
    ) -> None:
        """Log model errors with full context."""
        # Get agent name from callback context (may not always be available)
        agent_name = "Unknown"
        if hasattr(callback_context, 'agent') and callback_context.agent:
            agent_name = callback_context.agent.name
            
        logger.error(f"[ERROR] LLM Error in {agent_name}: {error}", exc_info=True)
        
        try:
            # Try to log the request if available in kwargs
            llm_request = kwargs.get('llm_request')
            if llm_request:
                logger.debug(f"Request that caused error:")
                request_data = {
                    'system_instruction': llm_request.system_instruction if hasattr(llm_request, 'system_instruction') else None,
                    'contents': [self._format_content(c) for c in llm_request.contents] if hasattr(llm_request, 'contents') else [],
                    'tools': [self._format_tool(t) for t in llm_request.tools] if hasattr(llm_request, 'tools') and llm_request.tools else []
                }
                log_llm_request(agent_name, request_data)
        except Exception as log_error:
            logger.error(f"Error logging error context: {log_error}")
    
    def _format_content(self, content):
        """Format content for logging."""
        try:
            return {
                'role': getattr(content, 'role', 'unknown'),
                'parts': [str(p) for p in getattr(content, 'parts', [])]
            }
        except Exception as e:
            logger.debug(f"Error formatting content: {e}")
            return {'error': str(e)}
    
    def _format_tool(self, tool):
        """Format tool definition for logging."""
        try:
            return {
                'name': tool.name if hasattr(tool, 'name') else str(tool),
                'parameters': str(tool.parameters) if hasattr(tool, 'parameters') else 'N/A'
            }
        except Exception as e:
            logger.debug(f"Error formatting tool: {e}")
            return {'error': str(e)}
    
    def _extract_function_calls(self, response):
        """Extract function calls from LLM response."""
        try:
            if not hasattr(response, 'candidates') or not response.candidates:
                return []
            
            function_calls = []
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            fc = part.function_call
                            function_calls.append({
                                'name': fc.name,
                                'args': dict(fc.args) if hasattr(fc, 'args') else {}
                            })
            return function_calls
        except Exception as e:
            logger.debug(f"Error extracting function calls: {e}")
            return []
    
    def _extract_usage(self, response):
        """Extract token usage from response."""
        try:
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                return {
                    'prompt_tokens': getattr(usage, 'prompt_token_count', 0),
                    'candidates_tokens': getattr(usage, 'candidates_token_count', 0),
                    'total_tokens': getattr(usage, 'total_token_count', 0)
                }
            return None
        except Exception as e:
            logger.debug(f"Error extracting usage: {e}")
            return None
