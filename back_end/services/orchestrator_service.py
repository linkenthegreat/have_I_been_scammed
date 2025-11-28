import json
import time  # Phase 3: Observability
import os
import logging
from agents_n_tools import agent
from agents_n_tools.tools import db_tools
from google.adk.runners import Runner
from google.genai import types
# Import session config instead of direct InMemorySessionService
from back_end.session_config import get_session_service
from back_end.observability import ObservabilityTracker  # Phase 3

logger = logging.getLogger(__name__)

class OrchestratorService:
    """
    Simplified orchestrator service using proper ADK multi-agent pattern.
    The orchestrator agent now contains all specialists as sub-agents.
    """
    
    def __init__(self):
        # Create the root orchestrator (contains all specialists as sub-agents)
        self.orchestrator = agent.get_orchestrator_agent()
        
        # Create session service (respects USE_DATABASE_SESSIONS env var)
        self.session_service = get_session_service()
        
        # Phase 4.5: Use ADK's built-in logging (set LOG_LEVEL=DEBUG for detailed LLM logs)
        # ADK provides excellent observability at DEBUG level:
        # - Full system instructions
        # - Complete conversation contents  
        # - All available functions
        # - LLM responses with usage metadata
        logger.info("[INFO] Using ADK's built-in logging. Set LOG_LEVEL=DEBUG for detailed LLM request/response logs.")
        
        # Create a single runner for the orchestrator
        # The orchestrator's LLM will decide which sub-agents to call
        self.runner = Runner(
            agent=self.orchestrator,
            app_name="scam_analyzer",
            session_service=self.session_service
        )

    async def process_user_request(self, session_id, user_input, input_type="text"):
        """
        Process user request using ADK's multi-agent orchestration.
        
        The orchestrator agent will:
        1. Analyze the request
        2. Call appropriate specialist sub-agents
        3. Coordinate their responses
        4. Return the final result
        
        Args:
            session_id: Unique session identifier
            user_input: User's input (text, URL, etc.)
            input_type: Type of input ("text", "url", "image", "mixed")
            
        Returns:
            dict: Analysis result with report and metadata
        """
        # Phase 3: Initialize observability tracker
        tracker = ObservabilityTracker(session_id)
        start_time = time.time()
        
        try:
            tracker.log_workflow_step('request_received', {
                'input_type': input_type,
                'session_id': session_id
            })
            
            # Create or get session
            try:
                session = await self.session_service.create_session(
                    app_name="scam_analyzer",
                    user_id="default",
                    session_id=session_id
                )
            except:
                session = await self.session_service.get_session(
                    app_name="scam_analyzer",
                    user_id="default",
                    session_id=session_id
                )
            
            # Get session history for context
            history = db_tools.get_recent_checks_direct(session_id, limit=3)
            history_context = ""
            if history:
                history_context = "\n\n**Recent Analysis History:**\n" + "\n".join(
                    [f"- [{h['date']}] {h['type']} ({h['risk']})" for h in history]
                )
            
            # Construct clean prompt (no session_id injection needed)
            prompt = f"""User Input: {user_input}{history_context}

Please analyze this for potential scams. Coordinate with specialist agents as needed."""
            
            query = types.Content(role="user", parts=[types.Part(text=prompt)])
            
            tracker.log_workflow_step('orchestrator_start', {
                'prompt_length': len(prompt),
                'has_history': bool(history_context)
            })
            
            # Run the orchestrator (it will call sub-agents as needed)
            response_text = ""
            final_event = None
            orchestrator_start = time.time()
            
            async for event in self.runner.run_async(
                user_id="default",
                session_id=session.id,
                new_message=query
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text and part.text != "None":
                            response_text += part.text
                final_event = event
            
            orchestrator_duration = int((time.time() - orchestrator_start) * 1000)
            tracker.log_event('agent_call', 
                agent_name='OrchestratorAgent',
                duration_ms=orchestrator_duration,
                metadata={'response_length': len(response_text)}
            )
            
            # Try to extract structured data from response
            analysis_result = self._extract_analysis(response_text)
            
            # Backend directly logs to database (no LLM involvement)
            check_id = None
            if analysis_result and analysis_result.get("risk_score"):
                tracker.log_workflow_step('analysis_complete', {
                    'risk_score': analysis_result.get("risk_score"),
                    'scam_type': analysis_result.get("scam_type")
                })
                
                # Backend handles logging directly (reliable, no LLM parsing needed)
                check_id = db_tools.log_check_direct(
                    session_id=session_id,
                    input_type=input_type,
                    content=user_input[:500],  # Truncate long content
                    risk_score=analysis_result.get("risk_score", "caution"),
                    scam_type=analysis_result.get("scam_type", "unknown"),
                    tags=",".join(analysis_result.get("tags", [])),
                    reasoning=analysis_result,
                    confidence=analysis_result.get("confidence", 0.0),
                    full_response=response_text  # Store complete agent output
                )
                
                total_duration = int((time.time() - start_time) * 1000)
                tracker.log_event('performance',
                    metadata={
                        'total_duration_ms': total_duration,
                        'check_id': check_id
                    }
                )
            
            # Always return response with check_id (if available)
            tracker.log_workflow_step('response_complete', {
                'has_analysis': bool(analysis_result),
                'has_check_id': bool(check_id)
            })
            
            return {
                "type": "analysis" if analysis_result else "chat",
                "check_id": check_id,  # Real check_id for export links (or None)
                "report": response_text,
                "message": response_text,  # Include for backwards compatibility
                "raw_analysis": analysis_result,
                "specialist": "Multi-Agent System",
                "session_id": session_id
            }
                
        except Exception as e:
            # Phase 3: Log error to observability system
            tracker.log_event('error',
                error_message=str(e),
                metadata={'traceback': __import__('traceback').format_exc()}
            )
            
            print(f"ERROR in orchestrator_service: {e}")
            import traceback
            traceback.print_exc()
            return {
                "type": "error",
                "message": f"An error occurred: {str(e)}",
                "error": str(e)
            }

    async def process_multimodal_request(self, content, session_id, input_type, context):
        """
        Process multimodal request with types.Content containing text + optional media.
        
        Args:
            content: types.Content with text + optional image + optional audio parts
            session_id: str - Unique session identifier
            input_type: str - ('text', 'url', 'image', 'audio', 'mixed')
            context: dict - User context (location, role, etc.)
        
        Returns:
            dict: Analysis result with report and metadata
        """
        # Phase 3: Initialize observability tracker
        tracker = ObservabilityTracker(session_id)
        start_time = time.time()
        
        try:
            tracker.log_workflow_step('multimodal_request_received', {
                'input_type': input_type,
                'has_context': bool(context)
            })
            
            # Create or get session
            try:
                session = await self.session_service.create_session(
                    app_name="scam_analyzer",
                    user_id="default",
                    session_id=session_id
                )
            except:
                session = await self.session_service.get_session(
                    app_name="scam_analyzer",
                    user_id="default",
                    session_id=session_id
                )
            
            # Get session history for context
            history = db_tools.get_recent_checks_direct(session_id, limit=3)
            history_text = ""
            if history:
                history_text = "\n\n**Recent Analysis History:**\n" + "\n".join(
                    [f"- [{h['date']}] {h['type']} ({h['risk']})" for h in history]
                )
            
            # Prepend clean prompt (no session_id injection)
            prompt_text = f"""Analyze this for potential scams.{history_text}"""
            
            # Insert prompt as first text part
            content.parts.insert(0, types.Part(text=prompt_text))
            
            # Run the orchestrator with multimodal content
            response_text = ""
            final_event = None
            
            async for event in self.runner.run_async(
                user_id="default",
                session_id=session.id,
                new_message=content
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text and part.text != "None":
                            response_text += part.text
                final_event = event
            
            # Extract structured analysis
            analysis_result = self._extract_analysis(response_text)
            
            # Build case summary with media indicators
            case_summary = self._build_case_summary(input_type, response_text, context)
            
            # Backend directly logs to database (always, if analysis exists)
            check_id = None
            if analysis_result and analysis_result.get("risk_score"):
                # Backend handles logging directly
                check_id = db_tools.log_check_direct(
                    session_id=session_id,
                    input_type=input_type,
                    content=case_summary[:500],
                    risk_score=analysis_result.get("risk_score", "caution"),
                    scam_type=analysis_result.get("scam_type", "unknown"),
                    tags=",".join(analysis_result.get("tags", [])),
                    reasoning=analysis_result,
                    confidence=analysis_result.get("confidence", 0.0),
                    full_response=response_text  # Store complete agent output
                )
            
            # Always return response with check_id (if available)
            return {
                "type": "analysis" if analysis_result else "chat",
                "check_id": check_id,  # Real check_id for export links (or None)
                "report": response_text,
                "message": response_text,  # Include for backwards compatibility
                "raw_analysis": analysis_result,
                "specialist": "Multi-Agent System (Multimodal)" if analysis_result else "OrchestratorAgent (Multimodal)",
                "session_id": session_id,
                "input_type": input_type
            }
                
        except Exception as e:
            print(f"ERROR in process_multimodal_request: {e}")
            import traceback
            traceback.print_exc()
            return {
                "type": "error",
                "message": f"An error occurred processing multimodal input: {str(e)}",
                "error": str(e)
            }
    
    def _build_case_summary(self, input_type, analysis, context):
        """Build human-readable case summary with media indicators"""
        parts = []
        
        if input_type == 'mixed':
            parts.append("📎 Multiple evidence types provided")
        elif input_type == 'image':
            parts.append("📷 Screenshot evidence analyzed")
        elif input_type == 'audio':
            parts.append("🎤 Audio recording analyzed")
        
        # Add truncated analysis
        summary = " | ".join(parts) if parts else ""
        if analysis:
            summary += f"\n\n{analysis[:500]}..."
        
        return summary

    def _extract_analysis(self, response_text):
        """
        Extract structured analysis from agent response.
        Looks for JSON blocks or structured data in the response.
        """
        try:
            # Try to find JSON in the response
            import re
            
            # Look for JSON code blocks
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Look for inline JSON objects
            json_match = re.search(r'\{[^{}]*"risk_score"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            # Check for structured indicators in text
            if any(keyword in response_text.lower() for keyword in ["risk:", "risk score:", "risk level:", "scam type:", "confidence:"]):
                # Extract basic info from text
                risk_score = "caution"
                text_lower = response_text.lower()
                
                # More flexible risk detection
                if any(phrase in text_lower for phrase in ["high risk", "risk level: high", "risk: high", "danger", "dangerous"]):
                    risk_score = "high"
                elif any(phrase in text_lower for phrase in ["safe", "legitimate", "low risk", "risk: safe"]):
                    risk_score = "safe"
                
                # Try to extract scam type
                scam_type = "unknown"
                if "phishing" in text_lower:
                    scam_type = "phishing"
                elif "job scam" in text_lower or "employment scam" in text_lower or "job offer scam" in text_lower:
                    scam_type = "job_scam"
                elif "romance" in text_lower:
                    scam_type = "romance_scam"
                elif "financial" in text_lower:
                    scam_type = "financial_scam"
                
                return {
                    "risk_score": risk_score,
                    "reasoning": response_text,
                    "scam_type": scam_type,
                    "tags": [],
                    "confidence": 0.8
                }
            
            return None
            
        except Exception as e:
            print(f"Error extracting analysis: {e}")
            return None

