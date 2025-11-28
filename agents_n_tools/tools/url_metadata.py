from urllib.parse import urlparse
import socket
import ssl
from datetime import datetime

def extract_url_metadata(url: str) -> dict:
    """
    Extracts metadata from a URL to detect suspicious characteristics.
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        dict: {
            "status": "success" | "error",
            "risk_level": "low" | "medium" | "high",
            "summary": str,
            "metadata": {
                "domain": str,
                "has_ssl": bool,
                "ssl_valid": bool | None,
                "suspicious_tld": bool,
                "ip_address": str | None
            },
            "red_flags": list[str]
        }
    """
    red_flags = []
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        
        # Check for suspicious TLDs
        suspicious_tlds = ['.xyz', '.tk', '.top', '.pw', '.cc', '.ga', '.cf', '.ml', '.gq']
        has_suspicious_tld = any(domain.endswith(tld) for tld in suspicious_tlds)
        if has_suspicious_tld:
            red_flags.append("Suspicious TLD (commonly used in scams)")
        
        # Check SSL
        has_ssl = parsed.scheme == 'https'
        ssl_valid = None
        
        if has_ssl:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((domain, 443), timeout=3) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        # Check certificate expiry
                        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        ssl_valid = not_after > datetime.now()
                        if not ssl_valid:
                            red_flags.append("SSL certificate expired")
            except Exception:
                ssl_valid = False
                red_flags.append("SSL certificate invalid or unreachable")
        else:
            red_flags.append("No HTTPS (insecure connection)")
        
        # Get IP address
        ip_address = None
        try:
            ip_address = socket.gethostbyname(domain)
        except socket.gaierror:
            red_flags.append("Domain does not resolve (possibly fake)")
        
        # Check for IP-based URL (suspicious)
        if domain.replace('.', '').isdigit():
            red_flags.append("URL uses IP address instead of domain name")
        
        # Check for excessively long domain (phishing tactic)
        if len(domain) > 50:
            red_flags.append("Unusually long domain name")
        
        # Check for multiple suspicious characters
        suspicious_chars = domain.count('-') + domain.count('_')
        if suspicious_chars > 3:
            red_flags.append("Excessive special characters in domain")
        
        # Calculate risk level based on red flags
        risk_level = "low"
        if len(red_flags) >= 3:
            risk_level = "high"
        elif len(red_flags) >= 1:
            risk_level = "medium"
        
        # Create human-readable summary
        if red_flags:
            flag_preview = ', '.join(red_flags[:3])
            if len(red_flags) > 3:
                flag_preview += f" (and {len(red_flags) - 3} more)"
            summary = f"Found {len(red_flags)} suspicious indicator(s): {flag_preview}"
        else:
            summary = "No suspicious indicators detected in URL metadata"
        
        return {
            "status": "success",
            "risk_level": risk_level,
            "summary": summary,
            "metadata": {
                "domain": domain,
                "has_ssl": has_ssl,
                "ssl_valid": ssl_valid,
                "suspicious_tld": has_suspicious_tld,
                "ip_address": ip_address
            },
            "red_flags": red_flags
        }
        
    except Exception as e:
        return {
            "status": "error",
            "risk_level": "unknown",
            "summary": f"Error analyzing URL: {str(e)}",
            "metadata": {
                "domain": "Unknown",
                "has_ssl": False,
                "ssl_valid": None,
                "suspicious_tld": False,
                "ip_address": None
            },
            "red_flags": [f"Error analyzing URL: {str(e)}"]
        }
