"""FHIR Operations - Shared utilities for FHIR resource operations"""
import requests
from core.config import Config
from core.logger import setup_logger

logger = setup_logger()


def fetch_token():
    """
    Fetch access token from SatuSehat OAuth2.
    
    Returns:
        tuple: (access_token, error_message or None)
    """
    token_url = f"{Config.AUTH_URL}/accesstoken?grant_type=client_credentials"
    try:
        resp = requests.post(
            token_url,
            data={
                "client_id": Config.CLIENT_ID,
                "client_secret": Config.CLIENT_SECRET
            },
            timeout=15
        )
        resp.raise_for_status()
        return resp.json().get("access_token"), None
    except Exception as e:
        logger.error(f"[FHIR] Failed to fetch token: {str(e)}")
        return None, str(e)


def fhir_get(url, token):
    """
    Helper method to perform GET request to FHIR server.
    
    Args:
        url (str): FHIR API endpoint URL
        token (str): Access token
        
    Returns:
        tuple: (response_json, status_code)
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/fhir+json"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        return resp.json(), resp.status_code
    except Exception as e:
        logger.error(f"[FHIR] GET request failed: {str(e)}")
        return {"error": str(e)}, 502


def post_fhir(url, token, resource):
    """
    POST FHIR resource to FHIR server (e.g., SatuSehat).
    
    Parameters:
        url (str): FHIR server endpoint URL
        token (str): OAuth2 access token
        resource (dict): FHIR resource object
        
    Returns:
        tuple: (response_body, http_status_code)
            - response_body: JSON response or raw text
            - http_status_code: HTTP status code
            
    Raises:
        - Network errors: Returns HTTP 502
        - JSON parse errors: Returns raw text response
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/fhir+json",
    }

    try:
        resp = requests.post(url, json=resource, headers=headers, timeout=20)
    except Exception as e:
        logger.error(f"[FHIR] Network error during POST: {str(e)}")
        return {"error": "Failed to POST resource", "detail": str(e)}, 502

    ctype = resp.headers.get("Content-Type", "")
    if "json" in ctype:
        try:
            return resp.json(), resp.status_code
        except Exception as e:
            logger.warning(f"[FHIR] Failed to parse JSON response: {str(e)}")
            return {"raw": resp.text}, resp.status_code

    return {"raw": resp.text}, resp.status_code
