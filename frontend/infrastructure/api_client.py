"""
API Client
==========
HTTP client for backend communication.
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import requests
    HAS_HTTPX = False

from .token_storage import TokenStorage, TokenData

logger = logging.getLogger(__name__)


class APIStatus(Enum):
    """API response status"""
    SUCCESS = "success"
    ERROR = "error"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"
    NETWORK_ERROR = "network_error"


@dataclass
class APIConfig:
    """API Configuration"""
    base_url: str = "http://localhost:8000"
    timeout: float = 30.0
    max_retries: int = 3
    
    @classmethod
    def from_env(cls):
        """Load from environment variables"""
        return cls(
            base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
            timeout=float(os.getenv("API_TIMEOUT", "30")),
            max_retries=int(os.getenv("API_MAX_RETRIES", "3"))
        )


class APIClient:
    """
    HTTP client for MusicMoodBot API.
    
    Features:
    - Automatic JWT token injection
    - Retry logic
    - Error handling
    """
    
    def __init__(self, config: APIConfig = None):
        self.config = config or APIConfig.from_env()
        self.token_storage = TokenStorage()
        self._flet_page = None
        
        if HAS_HTTPX:
            self._client = httpx.Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )
        else:
            self._client = None
        
        logger.info(f"API Client initialized: {self.config.base_url}")
    
    def set_flet_page(self, page):
        """Set Flet page for token storage"""
        self._flet_page = page
        self.token_storage.set_flet_page(page)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with auth token if available"""
        headers = {"Content-Type": "application/json"}
        
        try:
            token = self.token_storage.load()
            if token and token.is_valid():
                headers["Authorization"] = f"{token.token_type} {token.access_token}"
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
        
        return headers
    
    def get(self, path: str, params: Dict = None) -> Dict[str, Any]:
        """GET request"""
        try:
            url = f"{self.config.base_url}{path}"
            headers = self._get_headers()
            
            if HAS_HTTPX:
                response = self._client.get(path, params=params, headers=headers)
            else:
                response = requests.get(url, params=params, headers=headers, 
                                        timeout=self.config.timeout)
            
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"GET {path} failed: {e}")
            return {"status": APIStatus.NETWORK_ERROR, "error": str(e)}
    
    def post(self, path: str, data: Dict = None, json_data: Dict = None) -> Dict[str, Any]:
        """POST request"""
        try:
            url = f"{self.config.base_url}{path}"
            headers = self._get_headers()
            
            if HAS_HTTPX:
                response = self._client.post(path, json=json_data or data, headers=headers)
            else:
                response = requests.post(url, json=json_data or data, headers=headers,
                                         timeout=self.config.timeout)
            
            return self._handle_response(response)
            
        except Exception as e:
            logger.error(f"POST {path} failed: {e}")
            return {"status": APIStatus.NETWORK_ERROR, "error": str(e)}
    
    def _handle_response(self, response) -> Dict[str, Any]:
        """Handle HTTP response"""
        try:
            data = response.json()
        except Exception:
            data = {"raw": response.text}
        
        if response.status_code == 200:
            return {"status": APIStatus.SUCCESS, "data": data}
        elif response.status_code == 401:
            return {"status": APIStatus.UNAUTHORIZED, "error": "Unauthorized"}
        elif response.status_code == 404:
            return {"status": APIStatus.NOT_FOUND, "error": "Not found"}
        else:
            return {"status": APIStatus.ERROR, "error": data.get("detail", "Unknown error")}
    
    # ==================== CONVENIENCE METHODS ====================
    
    def health_check(self) -> bool:
        """Check if API is available"""
        try:
            result = self.get("/health")
            return result.get("status") == APIStatus.SUCCESS
        except Exception:
            return False
    
    def get_songs_by_mood(self, mood: str, limit: int = 20) -> List[Dict]:
        """Get songs by mood"""
        result = self.get(f"/api/moods/songs/by-mood/{mood}", {"limit": limit})
        if result.get("status") == APIStatus.SUCCESS:
            return result.get("data", [])
        return []
    
    def search_songs(self, query: str, limit: int = 10) -> List[Dict]:
        """Search songs"""
        result = self.get("/api/search/", {"q": query, "limit": limit})
        if result.get("status") == APIStatus.SUCCESS:
            return result.get("data", [])
        return []
    
    def detect_mood(self, text: str) -> Dict[str, Any]:
        """Detect mood from text"""
        result = self.post("/api/recommendations/detect-mood", {"text": text})
        if result.get("status") == APIStatus.SUCCESS:
            return result.get("data", {})
        return {}
    
    def smart_recommend(self, text: str, limit: int = 10) -> Dict[str, Any]:
        """Smart recommendation based on text"""
        result = self.post("/api/recommendations/smart", {
            "text": text,
            "limit": limit
        })
        if result.get("status") == APIStatus.SUCCESS:
            return result.get("data", {})
        return {}
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and store token"""
        result = self.post("/api/auth/login", {
            "username": username,
            "password": password
        })
        
        if result.get("status") == APIStatus.SUCCESS:
            data = result.get("data", {})
            if "access_token" in data:
                token = TokenData(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token", ""),
                    token_type=data.get("token_type", "Bearer")
                )
                self.token_storage.save(token)
        
        return result
    
    def logout(self):
        """Clear stored token"""
        self.token_storage.clear()


# Global API client instance
api = APIClient()
