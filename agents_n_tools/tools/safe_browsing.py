import os
import requests
from dotenv import load_dotenv

load_dotenv()

SAFE_BROWSING_API_KEY = os.getenv("SAFE_BROWSING_API_KEY")
SAFE_BROWSING_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

def check_url_safety(url: str) -> dict:
    """
    Checks a URL against Google Safe Browsing API.
    
    Args:
        url (str): The URL to check
        
    Returns:
        dict: {
            "status": "safe" | "malicious" | "error",
            "threat_type": "MALWARE" | "SOCIAL_ENGINEERING" | "UNWANTED_SOFTWARE" | None,
            "details": str
        }
    """
    if not SAFE_BROWSING_API_KEY:
        return {
            "status": "error",
            "threat_type": None,
            "details": "Safe Browsing API key not configured"
        }
    
    payload = {
        "client": {
            "clientId": "scam-prevention-tool",
            "clientVersion": "1.0.0"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    
    try:
        response = requests.post(
            f"{SAFE_BROWSING_URL}?key={SAFE_BROWSING_API_KEY}",
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        
        data = response.json()
        
        if "matches" in data and data["matches"]:
            threat = data["matches"][0]
            return {
                "status": "malicious",  # Changed from "threat_detected" for consistency
                "threat_type": threat.get("threatType"),
                "details": f"URL flagged as {threat.get('threatType')} by Google Safe Browsing"
            }
        else:
            return {
                "status": "safe",
                "threat_type": None,
                "details": "No threats detected by Google Safe Browsing"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "threat_type": None,
            "details": f"Error checking Safe Browsing: {str(e)}"
        }
