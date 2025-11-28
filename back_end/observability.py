"""
Observability layer for ADK agent system.
Tracks agent execution, tool usage, and performance metrics.

Phase 3: Observability System
- Agent execution tracking
- Tool invocation logging  
- Performance metrics
- Error tracking
- Workflow visualization data
"""
import sqlite3
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/observability.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
Path('logs').mkdir(exist_ok=True)

DB_PATH = Path(__file__).parent.parent / 'data' / 'scam_detection.db'


class ObservabilityTracker:
    """Tracks agent and tool execution for monitoring."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.db_path = DB_PATH
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Ensure observability_events table exists."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='observability_events'
            """)
            
            if not cursor.fetchone():
                logger.info("Creating observability_events table...")
                # Read and execute schema
                schema_path = Path(__file__).parent.parent / 'data' / 'schema.sql'
                with open(schema_path, 'r') as f:
                    schema = f.read()
                cursor.executescript(schema)
                logger.info("✅ Observability schema created")
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Schema setup error: {e}")
    
    def log_event(self, event_type: str, **kwargs):
        """
        Log an observability event to database.
        
        Args:
            event_type: Type of event ('agent_call', 'tool_call', 'error', 'performance', 'workflow')
            **kwargs: Additional event data (agent_name, tool_name, duration_ms, etc.)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO observability_events 
                (session_id, event_type, agent_name, tool_name, duration_ms,
                 input_data, output_data, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.session_id,
                event_type,
                kwargs.get('agent_name'),
                kwargs.get('tool_name'),
                kwargs.get('duration_ms'),
                json.dumps(kwargs.get('input_data', {})) if kwargs.get('input_data') else None,
                json.dumps(kwargs.get('output_data', {})) if kwargs.get('output_data') else None,
                kwargs.get('error_message'),
                json.dumps(kwargs.get('metadata', {})) if kwargs.get('metadata') else None
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Logged {event_type} event for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
    
    def track_agent_call(self, agent_name: str):
        """
        Decorator to track agent execution time and errors.
        
        Usage:
            @tracker.track_agent_call('TextAnalyzerAgent')
            async def analyze_text(text):
                ...
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.time()
                error = None
                result = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = str(e)
                    logger.error(f"Agent {agent_name} error: {error}")
                    raise
                finally:
                    duration = int((time.time() - start) * 1000)
                    self.log_event(
                        'agent_call',
                        agent_name=agent_name,
                        duration_ms=duration,
                        error_message=error,
                        metadata={'success': error is None}
                    )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.time()
                error = None
                result = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = str(e)
                    logger.error(f"Agent {agent_name} error: {error}")
                    raise
                finally:
                    duration = int((time.time() - start) * 1000)
                    self.log_event(
                        'agent_call',
                        agent_name=agent_name,
                        duration_ms=duration,
                        error_message=error,
                        metadata={'success': error is None}
                    )
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def track_tool_call(self, tool_name: str):
        """
        Decorator to track tool execution time and errors.
        
        Usage:
            @tracker.track_tool_call('check_url_safety')
            def check_url(url):
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                error = None
                result = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = str(e)
                    logger.error(f"Tool {tool_name} error: {error}")
                    raise
                finally:
                    duration = int((time.time() - start) * 1000)
                    self.log_event(
                        'tool_call',
                        tool_name=tool_name,
                        duration_ms=duration,
                        error_message=error,
                        metadata={'success': error is None}
                    )
            
            return wrapper
        return decorator
    
    def log_workflow_step(self, step_name: str, details: Dict[str, Any]):
        """
        Log a workflow step (e.g., agent transition, decision point).
        
        Args:
            step_name: Name of the workflow step
            details: Dictionary with step details
        """
        self.log_event(
            'workflow',
            metadata={
                'step': step_name,
                'details': details
            }
        )
        logger.info(f"Workflow: {step_name}")


def get_session_metrics(session_id: str) -> Dict[str, Any]:
    """
    Retrieve observability metrics for a session.
    
    Returns:
        Dictionary with agent stats, tool stats, error count, and total duration
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Agent call stats
        cursor.execute('''
            SELECT agent_name, COUNT(*), AVG(duration_ms), MAX(duration_ms), MIN(duration_ms)
            FROM observability_events
            WHERE session_id = ? AND event_type = 'agent_call'
            GROUP BY agent_name
        ''', (session_id,))
        agent_stats = [
            {
                'agent': row[0],
                'calls': row[1],
                'avg_duration_ms': round(row[2], 2) if row[2] else 0,
                'max_duration_ms': row[3],
                'min_duration_ms': row[4]
            }
            for row in cursor.fetchall()
        ]
        
        # Tool call stats
        cursor.execute('''
            SELECT tool_name, COUNT(*), AVG(duration_ms), MAX(duration_ms)
            FROM observability_events
            WHERE session_id = ? AND event_type = 'tool_call'
            GROUP BY tool_name
        ''', (session_id,))
        tool_stats = [
            {
                'tool': row[0],
                'calls': row[1],
                'avg_duration_ms': round(row[2], 2) if row[2] else 0,
                'max_duration_ms': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        # Error count
        cursor.execute('''
            SELECT COUNT(*)
            FROM observability_events
            WHERE session_id = ? AND error_message IS NOT NULL
        ''', (session_id,))
        error_count = cursor.fetchone()[0]
        
        # Total session duration
        cursor.execute('''
            SELECT MIN(timestamp), MAX(timestamp)
            FROM observability_events
            WHERE session_id = ?
        ''', (session_id,))
        times = cursor.fetchone()
        session_duration = None
        if times[0] and times[1]:
            start = datetime.fromisoformat(times[0])
            end = datetime.fromisoformat(times[1])
            session_duration = int((end - start).total_seconds() * 1000)
        
        conn.close()
        
        return {
            'session_id': session_id,
            'agent_stats': agent_stats,
            'tool_stats': tool_stats,
            'error_count': error_count,
            'session_duration_ms': session_duration
        }
    
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {
            'session_id': session_id,
            'error': str(e)
        }


def get_recent_errors(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent errors across all sessions.
    
    Args:
        limit: Maximum number of errors to return
        
    Returns:
        List of error events with context
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, session_id, event_type, agent_name, tool_name, 
                   error_message, metadata
            FROM observability_events
            WHERE error_message IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        errors = [
            {
                'timestamp': row[0],
                'session_id': row[1],
                'event_type': row[2],
                'agent_name': row[3],
                'tool_name': row[4],
                'error_message': row[5],
                'metadata': json.loads(row[6]) if row[6] else {}
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return errors
    
    except Exception as e:
        logger.error(f"Failed to get recent errors: {e}")
        return []


def get_performance_summary() -> Dict[str, Any]:
    """
    Get overall system performance summary.
    
    Returns:
        Dictionary with aggregate performance metrics
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_events,
                AVG(duration_ms) as avg_duration,
                MAX(duration_ms) as max_duration,
                COUNT(DISTINCT session_id) as unique_sessions
            FROM observability_events
            WHERE duration_ms IS NOT NULL
        ''')
        overall = cursor.fetchone()
        
        # Agent performance
        cursor.execute('''
            SELECT agent_name, COUNT(*), AVG(duration_ms)
            FROM observability_events
            WHERE event_type = 'agent_call' AND duration_ms IS NOT NULL
            GROUP BY agent_name
            ORDER BY AVG(duration_ms) DESC
        ''')
        agent_perf = [
            {'agent': row[0], 'calls': row[1], 'avg_duration_ms': round(row[2], 2)}
            for row in cursor.fetchall()
        ]
        
        # Tool performance
        cursor.execute('''
            SELECT tool_name, COUNT(*), AVG(duration_ms)
            FROM observability_events
            WHERE event_type = 'tool_call' AND duration_ms IS NOT NULL
            GROUP BY tool_name
            ORDER BY AVG(duration_ms) DESC
        ''')
        tool_perf = [
            {'tool': row[0], 'calls': row[1], 'avg_duration_ms': round(row[2], 2)}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'total_events': overall[0],
            'avg_duration_ms': round(overall[1], 2) if overall[1] else 0,
            'max_duration_ms': overall[2],
            'unique_sessions': overall[3],
            'agent_performance': agent_perf,
            'tool_performance': tool_perf
        }
    
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        return {'error': str(e)}
