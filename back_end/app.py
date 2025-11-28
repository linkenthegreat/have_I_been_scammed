import sys
import os
from pathlib import Path
import asyncio
import logging
from logging.handlers import RotatingFileHandler

# Add project root to Python path
# This allows running 'python back_end/app.py' or 'python app.py' from any depth
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from flask import Flask, request, jsonify, render_template
from back_end.services.orchestrator_service import OrchestratorService
from back_end import observability  # Phase 3: Observability
from agents_n_tools.tools import db_tools
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

# Phase 4.5: Enhanced Observability - Configure DEBUG-level logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # DEBUG for development, INFO for production
LOG_FILE = 'logs/adk_debug.log'

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure root logger with rotation
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        # Console handler (INFO and above)
        logging.StreamHandler(),
        # File handler (DEBUG and above) with rotation
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB per file
            backupCount=5           # Keep 5 old logs (50MB total)
        )
    ]
)

# Set ADK loggers to DEBUG for detailed LLM request/response logging
logging.getLogger('google_adk').setLevel(logging.DEBUG)
logging.getLogger('google_genai').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.info(f"[OK] Logging configured: Level={LOG_LEVEL}, File={LOG_FILE}")

app = Flask(__name__, 
            template_folder="../front_end/templates",
            static_folder="../front_end/static")

app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret")

# File upload configuration
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'aac'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit

# Initialize Service
orchestrator_service = OrchestratorService()

# Initialize DB on startup
db_tools.init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/observability')
def observability_dashboard():
    """Observability dashboard view (Phase 3)."""
    return render_template('observability.html')

def determine_input_type(text, url, image, audio):
    """Determine input_type based on what's provided"""
    has_text = bool(text)
    has_url = bool(url)
    has_image = bool(image and image.filename)
    has_audio = bool(audio and audio.filename)
    
    type_count = sum([has_text or has_url, has_image, has_audio])
    
    if type_count > 1:
        return 'mixed'
    elif has_image:
        return 'image'
    elif has_audio:
        return 'audio'
    elif has_url:
        return 'url'
    else:
        return 'text'

def build_content_parts(text, url, image_file, audio_file):
    """Build list of content parts for Gemini multimodal processing"""
    parts = []
    
    # Add text prompt
    prompt = "Analyze this potential scam"
    if text:
        prompt += f":\n\n{text}"
    if url:
        prompt += f"\n\nSuspicious URL: {url}"
    parts.append(types.Part(text=prompt))
    
    # Add image if provided
    if image_file and image_file.filename:
        image_bytes = image_file.read()
        parts.append(types.Part.from_bytes(
            data=image_bytes,
            mime_type=image_file.content_type or 'image/jpeg'
        ))
    
    # Add audio if provided
    if audio_file and audio_file.filename:
        audio_bytes = audio_file.read()
        parts.append(types.Part.from_bytes(
            data=audio_bytes,
            mime_type=audio_file.content_type or 'audio/mp3'
        ))
    
    return parts

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Analyze user input for potential scams using ADK multi-agent system.
    Supports multimodal input: text, URLs, images, and audio files.
    """
    # Check if this is multipart/form-data (file upload) or JSON
    is_multipart = request.content_type and 'multipart/form-data' in request.content_type
    
    if is_multipart:
        # Get form data
        session_id = request.form.get("session_id", "guest")
        text_input = request.form.get("content", "").strip()
        url_input = request.form.get("url", "").strip()
        user_location = request.form.get("user_location")
        user_role = request.form.get("user_role")
        
        # Get file uploads (optional)
        image_file = request.files.get('image_file')
        audio_file = request.files.get('audio_file')
        
        # Determine input type
        input_type = determine_input_type(text_input, url_input, image_file, audio_file)
        
        # Build multimodal content
        content_parts = build_content_parts(text_input, url_input, image_file, audio_file)
        content = types.Content(role="user", parts=content_parts)
        
        user_input = text_input or url_input or "[Multimodal input provided]"
        
    else:
        # Legacy JSON request format
        data = request.json
        session_id = data.get("session_id", "guest")
        user_input = data.get("content")
        input_type = data.get("type", "text")
        user_location = data.get("user_location")
        user_role = data.get("user_role")
        content = None
    
    if not user_input and not (is_multipart and content):
        return jsonify({"error": "No content provided"}), 400
    
    # Store user context if provided
    if user_location or user_role:
        db_tools.update_session_context_direct(session_id, user_location, user_role)
        
    try:
        if is_multipart and content:
            # Process multimodal request
            result = asyncio.run(orchestrator_service.process_multimodal_request(
                content=content,
                session_id=session_id,
                input_type=input_type,
                context={'location': user_location, 'role': user_role}
            ))
        else:
            # Process text-only request
            result = asyncio.run(orchestrator_service.process_user_request(session_id, user_input, input_type))
        
        # Add reporting resources if this was an analysis
        if result.get("type") == "analysis" and user_location:
            # Optionally enhance with location-specific resources
            # For now, use generic message
            result["reporting_resources"] = "Contact your local consumer protection agency for assistance."
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "type": "error"}), 500


@app.route('/api/feedback', methods=['POST'])
def feedback():
    data = request.json
    try:
        db_tools.add_feedback(
            check_id=data.get("check_id"),
            helpful=data.get("helpful"),
            comments=data.get("comments")
        )
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from back_end.services.export_service import ExportService
from flask import send_file

export_service = ExportService()

@app.route('/api/export/email')
def export_email():
    check_id = request.args.get('check_id')
    if not check_id:
        return jsonify({"error": "Missing check_id"}), 400
        
    check_data = db_tools.get_check(check_id)
    if not check_data or check_data.get("status") == "not_found":
        return jsonify({"error": "Check not found"}), 404
    
    # If check_data has a 'check' key (nested structure), use that
    if "check" in check_data and isinstance(check_data["check"], dict):
        check_data = check_data["check"]
        
    # We need to reconstruct reporting resources or fetch them if stored
    # For MVP, we might re-fetch or just use defaults if not stored separately
    # Ideally, we should have stored reporting_resources in DB, but we didn't add a column for it.
    # We can either add a column or just pass None/Defaults for now.
    # Let's pass None for now, the service handles defaults.
    
    # Wait, we can get the location from the session linked to the check to make it better?
    # db_tools.get_session_context(check_data['session_id']) -> then re-run resource assistant?
    # That's too expensive. Let's just use the basic export for now.
    
    eml_file = export_service.generate_eml(check_data)
    
    return send_file(
        eml_file,
        as_attachment=True,
        download_name=f"scam_report_{check_id}.eml",
        mimetype="message/rfc822"
    )

@app.route('/api/export/pdf')
def export_pdf():
    check_id = request.args.get('check_id')
    if not check_id:
        return jsonify({"error": "Missing check_id"}), 400
        
    check_data = db_tools.get_check(check_id)
    if not check_data or check_data.get("status") == "not_found":
        return jsonify({"error": "Check not found"}), 404
        
    # If check_data has a 'check' key (nested structure), use that
    if "check" in check_data and isinstance(check_data["check"], dict):
        check_data = check_data["check"]
        
    pdf_file = export_service.generate_pdf(check_data)
    
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=f"scam_report_{check_id}.pdf",
        mimetype="application/pdf"
    )

# Phase 3: Observability Endpoints

@app.route('/api/observability/metrics/<session_id>', methods=['GET'])
def get_session_observability(session_id):
    """Get observability metrics for a specific session."""
    try:
        metrics = observability.get_session_metrics(session_id)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/observability/errors', methods=['GET'])
def get_recent_errors_endpoint():
    """Get recent errors across all sessions."""
    try:
        limit = request.args.get('limit', 10, type=int)
        errors = observability.get_recent_errors(limit)
        return jsonify({"errors": errors})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/observability/performance', methods=['GET'])
def get_performance_endpoint():
    """Get overall system performance summary."""
    try:
        performance = observability.get_performance_summary()
        return jsonify(performance)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connectivity
        import sqlite3
        conn = sqlite3.connect('data/scam_detection.db')
        conn.close()
        
        return jsonify({
            "status": "healthy",
            "service": "scam_detection_api",
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

# Phase 4.5: Enhanced Observability - Log Viewing Endpoints
@app.route('/api/logs/recent', methods=['GET'])
def get_recent_logs():
    """Get recent DEBUG logs for troubleshooting."""
    try:
        lines = int(request.args.get('lines', 100))
        log_file = 'logs/adk_debug.log'
        
        if not os.path.exists(log_file):
            return jsonify({
                "error": "Log file not found",
                "message": "No logs available yet. Start using the system to generate logs."
            }), 404
        
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            log_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return jsonify({
            "logs": log_lines,
            "count": len(log_lines),
            "total_lines": len(all_lines),
            "file": log_file
        })
    except Exception as e:
        logger.error(f"Error reading logs: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/session/<session_id>', methods=['GET'])
def get_session_logs(session_id):
    """Get all logs for a specific session."""
    try:
        log_file = 'logs/adk_debug.log'
        
        if not os.path.exists(log_file):
            return jsonify({
                "error": "Log file not found",
                "message": "No logs available yet."
            }), 404
        
        session_logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if session_id in line:
                    session_logs.append(line)
        
        return jsonify({
            "session_id": session_id,
            "logs": session_logs,
            "count": len(session_logs)
        })
    except Exception as e:
        logger.error(f"Error reading session logs: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Phase 1.1: Watchdog Configuration
    # Control auto-reload behavior to prevent session disruption
    use_reloader = os.getenv('FLASK_USE_RELOADER', 'False').lower() == 'true'
    
    if use_reloader:
        print("⚠️  Flask auto-reload ENABLED - sessions may be disrupted during development")
        print("   To disable: Set FLASK_USE_RELOADER=False in .env")
    else:
        print("✅ Flask auto-reload DISABLED - sessions will persist during development")
        print("   To enable: Set FLASK_USE_RELOADER=True in .env")
    
    app.run(
        debug=True, 
        port=5000,
        use_reloader=use_reloader,  # Controlled by environment variable
        host='0.0.0.0'  # Allow external connections
    )
