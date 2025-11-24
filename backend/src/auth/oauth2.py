"""
OAuth2 authentication providers for OmniDoc
"""
import os
from typing import Optional, Dict
import httpx

# OAuth2 provider configurations
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")


async def verify_google_token(token: str) -> Optional[Dict]:
    """
    Verify Google OAuth2 token and get user info
    
    Args:
        token: Google OAuth2 access token
        
    Returns:
        User info dict or None if invalid
    """
    if not GOOGLE_CLIENT_ID:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            # Verify token with Google
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "provider": "google",
                    "provider_id": user_info.get("id"),
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture"),
                }
    except Exception:
        pass
    
    return None


async def verify_github_token(token: str) -> Optional[Dict]:
    """
    Verify GitHub OAuth2 token and get user info
    
    Args:
        token: GitHub OAuth2 access token
        
    Returns:
        User info dict or None if invalid
    """
    if not GITHUB_CLIENT_ID:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            # Verify token with GitHub
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "provider": "github",
                    "provider_id": str(user_info.get("id")),
                    "email": user_info.get("email"),
                    "name": user_info.get("name") or user_info.get("login"),
                    "picture": user_info.get("avatar_url"),
                }
    except Exception:
        pass
    
    return None

