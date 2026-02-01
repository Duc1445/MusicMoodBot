"""
Authentication service for MusicMoodBot
=========================================
Handles user login, signup, and session management
With JWT token-based authentication via API Client

Version: 2.0.0 (JWT Integration)
"""

import re
import hashlib
import secrets
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

# Import API client for JWT-based auth
from .api_client import api, token_storage, TokenData, APIStatus

# Import local state manager
from ..utils.state_manager import app_state

# Import backend for fallback/migration (will be removed in future)
try:
    from backend.src.database.database import add_user, get_user
    HAS_DIRECT_DB = True
except ImportError:
    HAS_DIRECT_DB = False


def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """
    Hash password using SHA-256 with salt.
    
    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    salted = f"{password}{salt}"
    hashed = hashlib.sha256(salted.encode('utf-8')).hexdigest()
    
    return hashed, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """
    Verify password against stored hash.
    """
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


class AuthService:
    """
    Handles authentication operations with JWT token management.
    
    Supports two modes:
    1. API-based authentication (recommended) - Uses JWT tokens via API
    2. Direct database access (legacy) - For backward compatibility
    
    The service automatically detects if the backend API is available
    and uses the appropriate method.
    """
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 6
    REQUIRE_UPPERCASE = False
    REQUIRE_LOWERCASE = False
    REQUIRE_DIGIT = False
    REQUIRE_SPECIAL = False
    
    # Authentication mode
    USE_API_AUTH = True  # Set to False to use direct DB access
    
    def __init__(self):
        self._flet_page = None
    
    def set_flet_page(self, page):
        """
        Set Flet page for secure token storage.
        Call this from main.py after page initialization.
        """
        self._flet_page = page
        token_storage.set_flet_page(page)
        api.set_flet_page(page)
    
    # ==================== VALIDATION ====================
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password.strip()) < AuthService.MIN_PASSWORD_LENGTH:
            return False, f"Mật khẩu phải có ít nhất {AuthService.MIN_PASSWORD_LENGTH} ký tự!"
        
        if AuthService.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "Mật khẩu phải có ít nhất 1 chữ hoa!"
        
        if AuthService.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "Mật khẩu phải có ít nhất 1 chữ thường!"
        
        if AuthService.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            return False, "Mật khẩu phải có ít nhất 1 số!"
        
        if AuthService.REQUIRE_SPECIAL:
            special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special for c in password):
                return False, "Mật khẩu phải có ít nhất 1 ký tự đặc biệt!"
        
        return True, ""
    
    # ==================== JWT API AUTHENTICATION ====================
    
    def login_with_api(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Login using JWT API authentication.
        
        Returns: (success: bool, message: str)
        """
        # Call login API
        response = api.auth.login(email, password)
        
        if response.is_success:
            data = response.data
            
            # Save JWT token
            api.save_token(
                access_token=data.get("access_token", ""),
                refresh_token=data.get("refresh_token", ""),
                expires_in=data.get("expires_in", 3600)
            )
            
            # Update local state with user info
            user_info = data.get("user", {})
            app_state.user_info["name"] = user_info.get("name", user_info.get("username", "User"))
            app_state.user_info["email"] = user_info.get("email", email)
            app_state.user_info["user_id"] = user_info.get("user_id", user_info.get("id"))
            app_state.user_info["last_login"] = datetime.now().isoformat()
            app_state.user_info["password"] = ""  # Never store password
            
            app_state.save_state()
            
            return True, "Đăng nhập thành công!"
        
        elif response.is_unauthorized:
            return False, "Email hoặc mật khẩu không chính xác!"
        
        elif response.status == APIStatus.NETWORK_ERROR:
            # Fallback to direct DB if API is unavailable
            if HAS_DIRECT_DB:
                return self.login_with_db(email, password)
            return False, "Không thể kết nối đến server. Vui lòng thử lại sau."
        
        else:
            return False, response.error_message or "Đăng nhập thất bại!"
    
    def signup_with_api(self, name: str, email: str, password: str) -> Tuple[bool, str]:
        """
        Register new user using API.
        
        Returns: (success: bool, message: str)
        """
        response = api.auth.signup(name, email, password)
        
        if response.is_success:
            data = response.data
            
            # Save JWT token if returned
            if data.get("access_token"):
                api.save_token(
                    access_token=data.get("access_token", ""),
                    refresh_token=data.get("refresh_token", ""),
                    expires_in=data.get("expires_in", 3600)
                )
            
            # Update local state
            user_info = data.get("user", {})
            app_state.user_info["name"] = name
            app_state.user_info["email"] = email
            app_state.user_info["user_id"] = user_info.get("user_id", user_info.get("id"))
            app_state.user_info["last_login"] = datetime.now().isoformat()
            app_state.user_info["password"] = ""
            
            app_state.save_state()
            
            return True, "Đăng ký thành công!"
        
        elif response.status_code == 409:
            return False, "Email đã tồn tại! Vui lòng dùng email khác."
        
        elif response.status == APIStatus.NETWORK_ERROR:
            if HAS_DIRECT_DB:
                return self.signup_with_db(name, email, password)
            return False, "Không thể kết nối đến server. Vui lòng thử lại sau."
        
        else:
            return False, response.error_message or "Đăng ký thất bại!"
    
    def refresh_token(self) -> bool:
        """
        Refresh the access token using refresh token.
        
        Returns: True if refresh successful
        """
        current_token = token_storage.load_token()
        if not current_token or not current_token.refresh_token:
            return False
        
        response = api.auth.refresh_token(current_token.refresh_token)
        
        if response.is_success:
            data = response.data
            api.save_token(
                access_token=data.get("access_token", ""),
                refresh_token=data.get("refresh_token", current_token.refresh_token),
                expires_in=data.get("expires_in", 3600)
            )
            return True
        
        return False
    
    # ==================== DIRECT DATABASE AUTH (Legacy) ====================
    
    def login_with_db(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Legacy login using direct database access.
        Will be deprecated in future versions.
        """
        if not HAS_DIRECT_DB:
            return False, "Database không khả dụng!"
        
        user = get_user(email)
        if not user:
            return False, "Email/username không tồn tại!"
        
        stored_password = user.get("password_hash", user.get("password", ""))
        
        if ":" in stored_password:
            stored_hash, salt = stored_password.split(":", 1)
            if not verify_password(password, stored_hash, salt):
                return False, "Mật khẩu không chính xác!"
        else:
            if stored_password != password:
                return False, "Mật khẩu không chính xác!"
            self._migrate_password(email, password)
        
        # Update state
        app_state.user_info["name"] = user.get("username", "User")
        app_state.user_info["email"] = user.get("email", "")
        app_state.user_info["user_id"] = user.get("user_id", None)
        app_state.user_info["last_login"] = datetime.now().isoformat()
        app_state.user_info["password"] = ""
        app_state.save_state()
        
        return True, "Đăng nhập thành công!"
    
    def signup_with_db(self, name: str, email: str, password: str) -> Tuple[bool, str]:
        """
        Legacy signup using direct database access.
        """
        if not HAS_DIRECT_DB:
            return False, "Database không khả dụng!"
        
        hashed, salt = hash_password(password)
        stored_format = f"{hashed}:{salt}"
        
        user_id = add_user(name, email, stored_format)
        if not user_id:
            return False, "Email đã tồn tại! Vui lòng dùng email khác."
        
        app_state.user_info["name"] = name
        app_state.user_info["email"] = email
        app_state.user_info["user_id"] = user_id
        app_state.user_info["last_login"] = datetime.now().isoformat()
        app_state.user_info["password"] = ""
        app_state.save_state()
        
        return True, "Đăng ký thành công!"
    
    @staticmethod
    def _migrate_password(email: str, plain_password: str):
        """Migrate plain text password to hashed format"""
        if not HAS_DIRECT_DB:
            return
        try:
            import sqlite3
            from backend.src.database.database import DB_PATH
            
            hashed, salt = hash_password(plain_password)
            stored_format = f"{hashed}:{salt}"
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ? OR email = ?",
                (stored_format, email, email)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Password migration failed: {e}")
    
    # ==================== PUBLIC INTERFACE ====================
    
    @staticmethod
    def login(email: str, password: str) -> Tuple[bool, str]:
        """
        Login user.
        
        Uses API authentication if available, falls back to direct DB.
        
        Returns: (success: bool, message: str)
        """
        if not email.strip():
            return False, "Vui lòng nhập email/username!"
        if not password.strip():
            return False, "Vui lòng nhập mật khẩu!"
        
        service = auth_service
        
        if AuthService.USE_API_AUTH:
            return service.login_with_api(email, password)
        else:
            return service.login_with_db(email, password)
    
    @staticmethod
    def signup(name: str, email: str, password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Register new user.
        
        Returns: (success: bool, message: str)
        """
        if not name.strip():
            return False, "Vui lòng nhập họ và tên!"
        if not email.strip():
            return False, "Vui lòng nhập email!"
        if not AuthService.is_valid_email(email):
            return False, "Email không hợp lệ! Vui lòng nhập email đúng định dạng (ví dụ: user@example.com)"
        if not password.strip():
            return False, "Vui lòng nhập mật khẩu!"
        
        is_valid, error_msg = AuthService.is_valid_password(password)
        if not is_valid:
            return False, error_msg
        
        if password != confirm_password:
            return False, "Mật khẩu không khớp!"
        
        service = auth_service
        
        if AuthService.USE_API_AUTH:
            return service.signup_with_api(name, email, password)
        else:
            return service.signup_with_db(name, email, password)
    
    @staticmethod
    def change_password(old_password: str, new_password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Change user password.
        
        Returns: (success: bool, message: str)
        """
        user_id = app_state.user_info.get("user_id")
        if not user_id:
            return False, "Bạn chưa đăng nhập!"
        
        # Validate new password
        is_valid, error_msg = AuthService.is_valid_password(new_password)
        if not is_valid:
            return False, error_msg
        
        if new_password != confirm_password:
            return False, "Mật khẩu mới không khớp!"
        
        if AuthService.USE_API_AUTH:
            response = api.auth.change_password(old_password, new_password)
            if response.is_success:
                return True, "Đổi mật khẩu thành công!"
            return False, response.error_message or "Đổi mật khẩu thất bại!"
        
        # Legacy DB approach
        if not HAS_DIRECT_DB:
            return False, "Không thể đổi mật khẩu!"
        
        email = app_state.user_info.get("email", "")
        user = get_user(email)
        if not user:
            return False, "Không tìm thấy người dùng!"
        
        stored_password = user.get("password", "")
        if ":" in stored_password:
            stored_hash, salt = stored_password.split(":", 1)
            if not verify_password(old_password, stored_hash, salt):
                return False, "Mật khẩu cũ không chính xác!"
        else:
            if stored_password != old_password:
                return False, "Mật khẩu cũ không chính xác!"
        
        try:
            import sqlite3
            from backend.src.database.database import DB_PATH
            
            hashed, salt = hash_password(new_password)
            stored_format = f"{hashed}:{salt}"
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password = ? WHERE user_id = ?",
                (stored_format, user_id)
            )
            conn.commit()
            conn.close()
            
            return True, "Đổi mật khẩu thành công!"
        except Exception as e:
            return False, f"Lỗi đổi mật khẩu: {str(e)}"
    
    @staticmethod
    def logout() -> Tuple[bool, str]:
        """Logout user and clear tokens"""
        # Clear JWT token
        api.clear_token()
        
        # Save preferences before logout
        app_state.save_state()
        
        # Reset state
        app_state.reset_user()
        app_state.reset_chat()
        
        return True, "Đã đăng xuất!"
    
    @staticmethod
    def is_logged_in() -> bool:
        """Check if user is logged in"""
        # First check JWT token
        if api.is_authenticated():
            return True
        
        # Fallback to local state
        return app_state.user_info.get("user_id") is not None
    
    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """Get current logged in user info"""
        if AuthService.is_logged_in():
            return {
                "user_id": app_state.user_info.get("user_id"),
                "name": app_state.user_info.get("name"),
                "email": app_state.user_info.get("email"),
                "last_login": app_state.user_info.get("last_login")
            }
        return None
    
    @staticmethod
    def get_auth_header() -> Dict[str, str]:
        """Get authorization header for API requests"""
        token = token_storage.load_token()
        if token and token.is_valid():
            return {"Authorization": f"{token.token_type} {token.access_token}"}
        return {}
    
    @staticmethod
    def ensure_authenticated() -> bool:
        """
        Ensure user is authenticated, refresh token if needed.
        
        Returns: True if user is authenticated
        """
        if not AuthService.is_logged_in():
            return False
        
        token = token_storage.load_token()
        if token and token.is_expired() and token.refresh_token:
            # Try to refresh
            return auth_service.refresh_token()
        
        return True


# Singleton instance
auth_service = AuthService()
