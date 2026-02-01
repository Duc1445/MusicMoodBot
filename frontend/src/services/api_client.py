"""
API Client Layer for MusicMoodBot Frontend
============================================
Provides a robust, async-ready HTTP client with:
- Automatic JWT token injection via interceptors
- Centralized error handling with retry logic
- Environment-based configuration
- Type-safe response handling

Author: MusicMoodBot Team
Version: 1.0.0
"""

import os
import asyncio
from typing import Optional, Dict, Any, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

# Try httpx first (preferred for async), fallback to requests
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    import requests
    HAS_HTTPX = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== CONFIGURATION ====================

class APIConfig:
    """API Configuration from environment variables"""
    
    # Default values (can be overridden via .env or environment)
    DEFAULT_BASE_URL = "http://localhost:8000"
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_MAX_RETRIES = 3
    
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL", self.DEFAULT_BASE_URL)
        self.timeout = float(os.getenv("API_TIMEOUT", self.DEFAULT_TIMEOUT))
        self.max_retries = int(os.getenv("API_MAX_RETRIES", self.DEFAULT_MAX_RETRIES))
        self.debug = os.getenv("API_DEBUG", "false").lower() == "true"
    
    @classmethod
    def from_env_file(cls, env_path: str = None):
        """Load configuration from .env file"""
        if env_path is None:
            # Look for .env in frontend directory
            env_path = os.path.join(
                os.path.dirname(__file__), "..", "..", ".env"
            )
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"\'')
        
        return cls()


# Global config instance
api_config = APIConfig.from_env_file()


# ==================== TOKEN STORAGE ====================

@dataclass
class TokenData:
    """JWT Token data container"""
    access_token: str = ""
    refresh_token: str = ""
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if access token is expired"""
        if self.expires_at is None:
            return False
        # Consider expired 1 minute before actual expiry
        return datetime.now() >= (self.expires_at - timedelta(minutes=1))
    
    def is_valid(self) -> bool:
        """Check if we have a valid token"""
        return bool(self.access_token) and not self.is_expired()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenData":
        """Create from dictionary"""
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at
        )


class TokenStorage:
    """
    Secure token storage abstraction.
    
    Supports multiple backends:
    - Flet's client_storage (recommended for Flet apps)
    - File-based storage (fallback)
    - Memory-only (for testing)
    """
    
    TOKEN_KEY = "mmb_auth_token"
    
    def __init__(self, storage_backend: str = "file"):
        """
        Initialize token storage.
        
        Args:
            storage_backend: "flet", "file", or "memory"
        """
        self._backend = storage_backend
        self._memory_store: Dict[str, Any] = {}
        self._token_file = os.path.join(
            os.path.dirname(__file__), "..", "..", ".auth_token"
        )
        self._flet_page = None
    
    def set_flet_page(self, page):
        """Set Flet page for client_storage access"""
        self._flet_page = page
        self._backend = "flet"
    
    def save_token(self, token_data: TokenData) -> bool:
        """Save token to storage"""
        try:
            data = token_data.to_dict()
            
            if self._backend == "flet" and self._flet_page:
                # Use Flet's client_storage (localStorage in web, secure storage on mobile)
                self._flet_page.client_storage.set(self.TOKEN_KEY, json.dumps(data))
            elif self._backend == "file":
                # File-based storage (for desktop apps)
                with open(self._token_file, 'w') as f:
                    json.dump(data, f)
            else:
                # Memory-only
                self._memory_store[self.TOKEN_KEY] = data
            
            logger.debug("Token saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            return False
    
    def load_token(self) -> Optional[TokenData]:
        """Load token from storage"""
        try:
            data = None
            
            if self._backend == "flet" and self._flet_page:
                stored = self._flet_page.client_storage.get(self.TOKEN_KEY)
                if stored:
                    data = json.loads(stored)
            elif self._backend == "file" and os.path.exists(self._token_file):
                with open(self._token_file, 'r') as f:
                    data = json.load(f)
            else:
                data = self._memory_store.get(self.TOKEN_KEY)
            
            if data:
                return TokenData.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
            return None
    
    def clear_token(self) -> bool:
        """Clear stored token"""
        try:
            if self._backend == "flet" and self._flet_page:
                self._flet_page.client_storage.remove(self.TOKEN_KEY)
            elif self._backend == "file" and os.path.exists(self._token_file):
                os.remove(self._token_file)
            else:
                self._memory_store.pop(self.TOKEN_KEY, None)
            
            logger.debug("Token cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear token: {e}")
            return False


# Global token storage
token_storage = TokenStorage(storage_backend="file")


# ==================== RESPONSE MODELS ====================

class APIStatus(Enum):
    """API Response status"""
    SUCCESS = "success"
    ERROR = "error"
    UNAUTHORIZED = "unauthorized"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"


@dataclass
class APIResponse:
    """
    Standardized API response wrapper.
    
    Provides consistent interface regardless of actual response format.
    """
    status: APIStatus
    data: Optional[Any] = None
    error_message: Optional[str] = None
    status_code: int = 0
    headers: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        return self.status == APIStatus.SUCCESS
    
    @property
    def is_unauthorized(self) -> bool:
        return self.status == APIStatus.UNAUTHORIZED or self.status_code == 401


# ==================== INTERCEPTORS ====================

class RequestInterceptor:
    """
    Request interceptor for modifying outgoing requests.
    
    Automatically adds:
    - Authorization header with JWT token
    - Content-Type header
    - Custom headers
    """
    
    def __init__(self, token_storage: TokenStorage):
        self._token_storage = token_storage
        self._custom_headers: Dict[str, str] = {}
    
    def add_header(self, key: str, value: str):
        """Add custom header to all requests"""
        self._custom_headers[key] = value
    
    def remove_header(self, key: str):
        """Remove custom header"""
        self._custom_headers.pop(key, None)
    
    def get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get all headers for request"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._custom_headers
        }
        
        if include_auth:
            token = self._token_storage.load_token()
            if token and token.is_valid():
                headers["Authorization"] = f"{token.token_type} {token.access_token}"
        
        return headers


class ResponseInterceptor:
    """
    Response interceptor for processing incoming responses.
    
    Handles:
    - Automatic token refresh on 401
    - Error logging
    - Response transformation
    """
    
    def __init__(self, on_unauthorized: Callable = None):
        self._on_unauthorized = on_unauthorized
    
    def process_response(self, response: APIResponse) -> APIResponse:
        """Process and potentially modify response"""
        if response.is_unauthorized:
            logger.warning("Received 401 Unauthorized response")
            if self._on_unauthorized:
                self._on_unauthorized()
        
        return response


# ==================== API CLIENT ====================

class APIClient:
    """
    Main API client for MusicMoodBot.
    
    Features:
    - Async-first design (with sync fallback)
    - Automatic retry with exponential backoff
    - Request/Response interceptors
    - Type-safe endpoint methods
    """
    
    def __init__(
        self,
        base_url: str = None,
        timeout: float = None,
        max_retries: int = None
    ):
        self.base_url = (base_url or api_config.base_url).rstrip('/')
        self.timeout = timeout or api_config.timeout
        self.max_retries = max_retries or api_config.max_retries
        
        # Initialize interceptors
        self.request_interceptor = RequestInterceptor(token_storage)
        self.response_interceptor = ResponseInterceptor(
            on_unauthorized=self._handle_unauthorized
        )
        
        # Async client (created on demand)
        self._async_client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"API Client initialized: {self.base_url}")
    
    def _handle_unauthorized(self):
        """Handle 401 unauthorized - try to refresh token"""
        logger.info("Handling unauthorized - attempting token refresh")
        # Token refresh logic will be handled by auth_service
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint"""
        if endpoint.startswith('http'):
            return endpoint
        return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    # ==================== SYNC METHODS ====================
    
    def request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        include_auth: bool = True,
        retry_count: int = 0
    ) -> APIResponse:
        """
        Make a synchronous HTTP request.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to base_url)
            data: Request body (for POST/PUT)
            params: Query parameters
            include_auth: Whether to include Authorization header
            retry_count: Current retry attempt number
            
        Returns:
            APIResponse with standardized format
        """
        url = self._build_url(endpoint)
        headers = self.request_interceptor.get_headers(include_auth)
        
        if api_config.debug:
            logger.debug(f"Request: {method} {url}")
            logger.debug(f"Headers: {headers}")
            if data:
                logger.debug(f"Body: {data}")
        
        try:
            if HAS_HTTPX:
                # Use httpx sync client
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=data,
                        params=params
                    )
            else:
                # Fallback to requests
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )
            
            return self._process_response(response)
            
        except (httpx.TimeoutException if HAS_HTTPX else requests.Timeout) as e:
            logger.error(f"Request timeout: {e}")
            if retry_count < self.max_retries:
                return self.request(
                    method, endpoint, data, params, include_auth, retry_count + 1
                )
            return APIResponse(
                status=APIStatus.TIMEOUT,
                error_message=f"Request timed out after {self.max_retries} retries"
            )
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            if retry_count < self.max_retries:
                return self.request(
                    method, endpoint, data, params, include_auth, retry_count + 1
                )
            return APIResponse(
                status=APIStatus.NETWORK_ERROR,
                error_message=str(e)
            )
    
    def _process_response(self, response) -> APIResponse:
        """Process HTTP response into APIResponse"""
        status_code = response.status_code
        
        try:
            if HAS_HTTPX:
                data = response.json() if response.content else None
                headers = dict(response.headers)
            else:
                data = response.json() if response.content else None
                headers = dict(response.headers)
        except (json.JSONDecodeError, ValueError):
            data = response.text if hasattr(response, 'text') else str(response.content)
            headers = {}
        
        # Determine status
        if 200 <= status_code < 300:
            status = APIStatus.SUCCESS
            error_msg = None
        elif status_code == 401:
            status = APIStatus.UNAUTHORIZED
            error_msg = data.get("detail", "Unauthorized") if isinstance(data, dict) else "Unauthorized"
        else:
            status = APIStatus.ERROR
            error_msg = data.get("detail", str(data)) if isinstance(data, dict) else str(data)
        
        api_response = APIResponse(
            status=status,
            data=data,
            error_message=error_msg,
            status_code=status_code,
            headers=headers
        )
        
        return self.response_interceptor.process_response(api_response)
    
    # ==================== ASYNC METHODS ====================
    
    async def _get_async_client(self) -> "httpx.AsyncClient":
        """Get or create async client"""
        if not HAS_HTTPX:
            raise RuntimeError("httpx is required for async requests")
        
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(timeout=self.timeout)
        return self._async_client
    
    async def request_async(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        include_auth: bool = True,
        retry_count: int = 0
    ) -> APIResponse:
        """
        Make an asynchronous HTTP request.
        
        Same parameters as sync request method.
        """
        if not HAS_HTTPX:
            # Fallback to sync for non-httpx
            return self.request(method, endpoint, data, params, include_auth, retry_count)
        
        url = self._build_url(endpoint)
        headers = self.request_interceptor.get_headers(include_auth)
        
        try:
            client = await self._get_async_client()
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params
            )
            return self._process_response(response)
            
        except httpx.TimeoutException as e:
            logger.error(f"Async request timeout: {e}")
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self.request_async(
                    method, endpoint, data, params, include_auth, retry_count + 1
                )
            return APIResponse(
                status=APIStatus.TIMEOUT,
                error_message=f"Request timed out after {self.max_retries} retries"
            )
            
        except Exception as e:
            logger.error(f"Async request failed: {e}")
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self.request_async(
                    method, endpoint, data, params, include_auth, retry_count + 1
                )
            return APIResponse(
                status=APIStatus.NETWORK_ERROR,
                error_message=str(e)
            )
    
    async def close(self):
        """Close async client"""
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
    
    # ==================== CONVENIENCE METHODS ====================
    
    def get(self, endpoint: str, params: Dict = None, **kwargs) -> APIResponse:
        """GET request"""
        return self.request("GET", endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Dict = None, **kwargs) -> APIResponse:
        """POST request"""
        return self.request("POST", endpoint, data=data, **kwargs)
    
    def put(self, endpoint: str, data: Dict = None, **kwargs) -> APIResponse:
        """PUT request"""
        return self.request("PUT", endpoint, data=data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> APIResponse:
        """DELETE request"""
        return self.request("DELETE", endpoint, **kwargs)
    
    def patch(self, endpoint: str, data: Dict = None, **kwargs) -> APIResponse:
        """PATCH request"""
        return self.request("PATCH", endpoint, data=data, **kwargs)
    
    # Async versions
    async def get_async(self, endpoint: str, params: Dict = None, **kwargs) -> APIResponse:
        """Async GET request"""
        return await self.request_async("GET", endpoint, params=params, **kwargs)
    
    async def post_async(self, endpoint: str, data: Dict = None, **kwargs) -> APIResponse:
        """Async POST request"""
        return await self.request_async("POST", endpoint, data=data, **kwargs)
    
    async def put_async(self, endpoint: str, data: Dict = None, **kwargs) -> APIResponse:
        """Async PUT request"""
        return await self.request_async("PUT", endpoint, data=data, **kwargs)
    
    async def delete_async(self, endpoint: str, **kwargs) -> APIResponse:
        """Async DELETE request"""
        return await self.request_async("DELETE", endpoint, **kwargs)


# ==================== TYPED API ENDPOINTS ====================

class MoodAPI:
    """Typed methods for Mood API endpoints"""
    
    def __init__(self, client: APIClient):
        self._client = client
    
    def health_check(self) -> APIResponse:
        """Check API health"""
        return self._client.get("/health", include_auth=False)
    
    def predict_mood(self, song_data: Dict) -> APIResponse:
        """Predict mood for a song"""
        return self._client.post("/api/moods/predict", data=song_data)
    
    def get_songs_by_mood(self, mood: str) -> APIResponse:
        """Get songs by mood"""
        return self._client.get(f"/api/moods/songs/by-mood/{mood}")
    
    def smart_recommend(self, text: str, user_id: str = None, limit: int = 10) -> APIResponse:
        """Get smart recommendations based on text"""
        return self._client.post("/api/moods/smart-recommend", data={
            "text": text,
            "user_id": user_id,
            "limit": limit
        })
    
    def search_songs(self, query: str, limit: int = 10) -> APIResponse:
        """Search songs"""
        return self._client.get("/api/moods/search", params={
            "query": query,
            "limit": limit
        })
    
    def get_mood_stats(self) -> APIResponse:
        """Get mood statistics"""
        return self._client.get("/api/moods/stats")
    
    def get_all_moods(self) -> APIResponse:
        """Get all available moods"""
        return self._client.get("/api/moods/all")


class AuthAPI:
    """Typed methods for Authentication API endpoints"""
    
    def __init__(self, client: APIClient):
        self._client = client
    
    def login(self, email: str, password: str) -> APIResponse:
        """Login and get JWT token"""
        return self._client.post("/api/v2/auth/login", data={
            "email": email,
            "password": password
        }, include_auth=False)
    
    def signup(self, name: str, email: str, password: str) -> APIResponse:
        """Register new user"""
        return self._client.post("/api/v2/auth/signup", data={
            "name": name,
            "email": email,
            "password": password
        }, include_auth=False)
    
    def refresh_token(self, refresh_token: str) -> APIResponse:
        """Refresh access token"""
        return self._client.post("/api/v2/auth/refresh", data={
            "refresh_token": refresh_token
        }, include_auth=False)
    
    def logout(self) -> APIResponse:
        """Logout and invalidate token"""
        return self._client.post("/api/v2/auth/logout")
    
    def get_me(self) -> APIResponse:
        """Get current user info"""
        return self._client.get("/api/v2/auth/me")
    
    def change_password(self, old_password: str, new_password: str) -> APIResponse:
        """Change user password"""
        return self._client.post("/api/v2/auth/change-password", data={
            "old_password": old_password,
            "new_password": new_password
        })


class PlaylistAPI:
    """Typed methods for Playlist API endpoints"""
    
    def __init__(self, client: APIClient):
        self._client = client
    
    def get_playlists(self, user_id: str) -> APIResponse:
        """Get user's playlists"""
        return self._client.get(f"/api/v2/playlists", params={"user_id": user_id})
    
    def create_playlist(self, name: str, user_id: str, song_ids: list = None) -> APIResponse:
        """Create new playlist"""
        return self._client.post("/api/v2/playlists", data={
            "name": name,
            "user_id": user_id,
            "song_ids": song_ids or []
        })
    
    def add_song_to_playlist(self, playlist_id: int, song_id: int) -> APIResponse:
        """Add song to playlist"""
        return self._client.post(f"/api/v2/playlists/{playlist_id}/songs", data={
            "song_id": song_id
        })
    
    def remove_song_from_playlist(self, playlist_id: int, song_id: int) -> APIResponse:
        """Remove song from playlist"""
        return self._client.delete(f"/api/v2/playlists/{playlist_id}/songs/{song_id}")


class AnalyticsAPI:
    """Typed methods for Analytics API endpoints"""
    
    def __init__(self, client: APIClient):
        self._client = client
    
    def get_user_insights(self, user_id: str) -> APIResponse:
        """Get user insights and analytics"""
        return self._client.get(f"/api/v2/analytics/user/{user_id}")
    
    def get_listening_history(self, user_id: str, limit: int = 50) -> APIResponse:
        """Get user listening history"""
        return self._client.get(f"/api/v2/analytics/history/{user_id}", params={
            "limit": limit
        })
    
    def record_listen(self, user_id: str, song_id: int) -> APIResponse:
        """Record song listen event"""
        return self._client.post("/api/v2/analytics/listen", data={
            "user_id": user_id,
            "song_id": song_id
        })


# ==================== GLOBAL API INSTANCE ====================

class API:
    """
    Main API facade providing access to all endpoint groups.
    
    Usage:
        from src.services.api_client import api
        
        # Health check
        result = api.moods.health_check()
        
        # Login
        result = api.auth.login("email@example.com", "password")
        if result.is_success:
            token_storage.save_token(TokenData(
                access_token=result.data["access_token"],
                refresh_token=result.data["refresh_token"]
            ))
        
        # Get recommendations
        result = api.moods.smart_recommend("I feel happy today")
    """
    
    def __init__(self, base_url: str = None):
        self._client = APIClient(base_url=base_url)
        self.moods = MoodAPI(self._client)
        self.auth = AuthAPI(self._client)
        self.playlists = PlaylistAPI(self._client)
        self.analytics = AnalyticsAPI(self._client)
    
    @property
    def client(self) -> APIClient:
        """Access the underlying HTTP client"""
        return self._client
    
    def set_flet_page(self, page):
        """Set Flet page for secure token storage"""
        token_storage.set_flet_page(page)
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        token = token_storage.load_token()
        return token is not None and token.is_valid()
    
    def get_token(self) -> Optional[TokenData]:
        """Get current token"""
        return token_storage.load_token()
    
    def save_token(self, access_token: str, refresh_token: str = "", expires_in: int = 3600):
        """Save authentication token"""
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        token_data = TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        token_storage.save_token(token_data)
    
    def clear_token(self):
        """Clear authentication token (logout)"""
        token_storage.clear_token()


# Global API instance
api = API()


# ==================== HELPER FUNCTIONS ====================

def configure_api(base_url: str = None, flet_page=None):
    """
    Configure API client.
    
    Call this at app startup to configure the API.
    
    Args:
        base_url: Override default base URL
        flet_page: Flet page for secure token storage
    """
    global api
    
    if base_url:
        api = API(base_url=base_url)
    
    if flet_page:
        api.set_flet_page(flet_page)
    
    return api


# Export public interface
__all__ = [
    'api',
    'API',
    'APIClient', 
    'APIResponse',
    'APIStatus',
    'TokenData',
    'TokenStorage',
    'token_storage',
    'api_config',
    'configure_api'
]
