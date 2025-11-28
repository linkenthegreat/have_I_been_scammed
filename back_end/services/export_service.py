import json
from email.message import EmailMessage
from fpdf import FPDF
import io

class ExportService:
    def generate_eml(self, check_data):
        """Generates an .eml file for the scam report."""
        msg = EmailMessage()
        
        scam_type = check_data.get('scam_type', 'Suspicious Activity')
        risk_score = check_data.get('risk_score', 'Unknown')
        
        # Try to extract formal email from full_response first
        full_response = check_data.get('full_response', '')
        email_body = self._extract_formal_email(full_response)
        
        # Extract recipient from email body (looks for "To: agency@email.com")
        recipient = self._extract_recipient(email_body if email_body else full_response)
        if not recipient:
            recipient = "reportphishing@apwg.org"  # Fallback
             
        msg['To'] = recipient
        msg['Subject'] = f"Scam Report: {scam_type} ({risk_score.upper()} Risk)"
        msg['From'] = "user@example.com"  # Placeholder, user will send from their own
        
        # If no formal email found, construct from structured data
        if not email_body:
            # Parse agent_reasoning to extract clean text
            reasoning = check_data.get('agent_reasoning')
            if isinstance(reasoning, str):
                try:
                    reasoning = json.loads(reasoning)
                except:
                    pass
            
            # Extract reasoning text from JSON or use as-is
            if isinstance(reasoning, dict):
                reasoning_text = reasoning.get("reasoning", str(reasoning))
            else:
                reasoning_text = str(reasoning)
            
            # Construct fallback body
            email_body = f"""I am reporting a potential scam.

--- Analysis Summary ---
Risk Level: {risk_score.upper()}
Scam Type: {scam_type}
Date Detected: {check_data.get('created_at')}

--- Suspicious Content ---
{check_data.get('input_content')}

--- Analysis Details ---
{reasoning_text}

Please investigate this matter."""
        
        msg.set_content(email_body)
        
        return io.BytesIO(msg.as_bytes())
    
    def _extract_formal_email(self, full_response):
        """
        Extracts the formal law enforcement email section from agent response.
        Looks for markers like 'FORMAL LAW ENFORCEMENT EMAIL' or email structure.
        """
        if not full_response:
            return None
        
        # Look for formal email section markers
        markers = [
            '**FORMAL LAW ENFORCEMENT EMAIL**',
            'FORMAL LAW ENFORCEMENT EMAIL',
            'Here is the draft email',
            'drafted email for you',
            '\n\nTo:',
            '\nTo: '
        ]
        
        start_idx = -1
        for marker in markers:
            idx = full_response.find(marker)
            if idx != -1:
                start_idx = idx
                # If we found a header marker, skip past it
                if '**' in marker or 'draft' in marker.lower():
                    start_idx = full_response.find('\n', start_idx) + 1
                break
        
        if start_idx == -1:
            return None
        
        # Extract from marker to end of formal email
        email_text = full_response[start_idx:]
        
        # Find where formal email ends (usually marked by --- or next section)
        end_markers = [
            '\n\n---\n\n**',
            '\n\n### Primary Reporting',
            '\n\n### Victim Support',
            '\n\n**Summary of Steps',
            '\n\nWould you like'
        ]
        
        end_idx = len(email_text)
        for marker in end_markers:
            idx = email_text.find(marker)
            if idx != -1 and idx < end_idx:
                end_idx = idx
        
        formal_email = email_text[:end_idx].strip()
        
        # Clean up markdown and extra formatting
        formal_email = formal_email.replace('**FORMAL LAW ENFORCEMENT EMAIL**', '').strip()
        
        # Remove excessive newlines
        while '\n\n\n' in formal_email:
            formal_email = formal_email.replace('\n\n\n', '\n\n')
        
        return formal_email if len(formal_email) > 50 else None
    
    def _extract_recipient(self, text):
        """Extract email recipient from agent's formatted email."""
        if not text:
            return None
        
        # Look for patterns like "To: email@domain.com" or "Contact: email@domain.com"
        import re
        patterns = [
            r'To:\s*([\w\.-]+@[\w\.-]+\.\w+)',  # To: email@example.com
            r'Contact:\s*([\w\.-]+@[\w\.-]+\.\w+)',  # Contact: email@example.com
            r'Agency.*?Contact:\s*([\w\.-]+@[\w\.-]+\.\w+)',  # Agency ... Contact: email
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def generate_pdf(self, check_data):
        """Generates a PDF report."""
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 10, "Scam Analysis Report", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)
        
        # Risk Badge
        risk_score = check_data.get('risk_score', 'unknown').upper()
        color = (220, 38, 38) if risk_score == "HIGH" else (202, 138, 4) if risk_score == "CAUTION" else (22, 163, 74)
        pdf.set_text_color(*color)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"RISK LEVEL: {risk_score}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # Details
        pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(pdf.epw, 10, f"Scam Type: {check_data.get('scam_type')}")
        pdf.multi_cell(pdf.epw, 10, f"Date: {check_data.get('created_at')}")
        pdf.ln(5)
        
        # Content
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Analyzed Content:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Courier", "", 10)
        # Sanitize content to avoid encoding issues
        content = str(check_data.get('input_content', '')).encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(pdf.epw, 5, content)
        pdf.ln(5)
        
        # Reasoning
        reasoning = check_data.get('agent_reasoning')
        if isinstance(reasoning, str):
            try:
                reasoning = json.loads(reasoning)
            except:
                pass
        
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Analysis Details:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        
        if isinstance(reasoning, dict):
            reasoning_text = reasoning.get("reasoning", str(reasoning))
        else:
            reasoning_text = str(reasoning)
            
        # Sanitize reasoning text
        reasoning_text = reasoning_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(pdf.epw, 6, reasoning_text)
        pdf.ln(10)
                
        return io.BytesIO(pdf.output())