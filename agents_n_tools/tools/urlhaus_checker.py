import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

URLHAUS_API_URL = "https://urlhaus-api.abuse.ch/v1/url/"
URLHAUS_API_KEY = os.getenv("URLHAUS_API_KEY")

def check_urlhaus(url: str) -> dict:
    """
    Checks a URL against the URLhaus malware database.
    
    Args:
        url (str): The URL to check
        
    Returns:
        dict: {
            "status": "safe" | "malicious" | "error",
            "threat_type": str | None,
            "details": str,
            "url_status": str | None,  # online/offline/unknown
            "blacklists": dict | None,  # Spamhaus DBL and SURBL status
            "tags": list | None,  # Malware family tags
            "date_added": str | None,  # When first reported
            "reporter": str | None  # Who reported it
        }
    """
    if not URLHAUS_API_KEY:
        return {
            "status": "error",
            "threat_type": None,
            "details": "URLhaus API key not configured in .env file",
            "url_status": None,
            "blacklists": None,
            "tags": None,
            "date_added": None,
            "reporter": None
        }
    
    try:
        headers = {"Auth-Key": URLHAUS_API_KEY}
        response = requests.post(
            URLHAUS_API_URL,
            data={"url": url},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("query_status") == "ok":
            # URL found in URLhaus database (malicious)
            threat_type = data.get("threat", "Unknown malware")
            url_status = data.get("url_status", "unknown")
            blacklists = data.get("blacklists", {})
            tags = data.get("tags", [])
            date_added = data.get("date_added", "Unknown")
            reporter = data.get("reporter", "Unknown")
            
            # Build detailed description
            details_parts = [f"⚠️ URL reported to URLhaus as {threat_type}"]
            details_parts.append(f"Status: {url_status}")
            
            if blacklists:
                if blacklists.get("spamhaus_dbl") and blacklists["spamhaus_dbl"] != "not listed":
                    details_parts.append(f"Spamhaus DBL: {blacklists['spamhaus_dbl']}")
                if blacklists.get("surbl") == "listed":
                    details_parts.append("SURBL: listed")
            
            if tags:
                details_parts.append(f"Tags: {', '.join(tags)}")
            
            details_parts.append(f"First seen: {date_added}")
            details_parts.append(f"Reported by: {reporter}")
            
            return {
                "status": "malicious",
                "threat_type": threat_type,
                "details": " | ".join(details_parts),
                "url_status": url_status,
                "blacklists": blacklists,
                "tags": tags,
                "date_added": date_added,
                "reporter": reporter
            }
        elif data.get("query_status") == "no_results":
            # URL not in database (likely safe)
            return {
                "status": "safe",
                "threat_type": None,
                "details": "✓ No matches in URLhaus malware database",
                "url_status": None,
                "blacklists": None,
                "tags": None,
                "date_added": None,
                "reporter": None
            }
        else:
            query_status = data.get("query_status", "unknown")
            return {
                "status": "error",
                "threat_type": None,
                "details": f"Unexpected URLhaus response: {query_status}",
                "url_status": None,
                "blacklists": None,
                "tags": None,
                "date_added": None,
                "reporter": None
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "threat_type": None,
            "details": f"Error checking URLhaus: {str(e)}",
            "url_status": None,
            "blacklists": None,
            "tags": None,
            "date_added": None,
            "reporter": None
        }
