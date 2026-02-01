"""
Token Storage
=============
Secure token storage for JWT tokens.
"""

import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


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
        self._backend = storage_backend
        self._memory_store: Dict[str, Any] = {}
        self._token_file = os.path.join(
            os.path.dirname(__file__), "..", ".auth_token"
        )
        self._flet_page = None
    
    def set_flet_page(self, page):
        """Set Flet page for client_storage access"""
        self._flet_page = page
        self._backend = "flet"
    
    def save(self, token: TokenData) -> bool:
        """Save token to storage"""
        try:
            data = token.to_dict()
            
            if self._backend == "flet" and self._flet_page:
                try:
                    self._flet_page.client_storage.set(self.TOKEN_KEY, json.dumps(data))
                    return True
                except Exception as e:
                    logger.warning(f"Flet storage failed, using file: {e}")
            
            # Fallback to file
            with open(self._token_file, 'w') as f:
                json.dump(data, f)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            return False
    
    def load(self) -> Optional[TokenData]:
        """Load token from storage"""
        try:
            data = None
            
            if self._backend == "flet" and self._flet_page:
                try:
                    raw = self._flet_page.client_storage.get(self.TOKEN_KEY)
                    if raw:
                        data = json.loads(raw)
                except Exception as e:
                    logger.warning(f"Flet load failed: {e}")
            
            if data is None and os.path.exists(self._token_file):
                with open(self._token_file, 'r') as f:
                    data = json.load(f)
            
            if data:
                return TokenData.from_dict(data)
            
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
        
        return None
    
    def clear(self) -> bool:
        """Clear stored token"""
        try:
            if self._backend == "flet" and self._flet_page:
                try:
                    self._flet_page.client_storage.remove(self.TOKEN_KEY)
                except Exception:
                    pass
            
            if os.path.exists(self._token_file):
                os.remove(self._token_file)
            
            self._memory_store.clear()
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear token: {e}")
            return False
    
    def has_token(self) -> bool:
        """Check if a token exists"""
        token = self.load()
        return token is not None and token.is_valid()
