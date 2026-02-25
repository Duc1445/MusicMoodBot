"""
Authentication service for MusicMoodBot
Handles user login, signup, and session management
Integrated with v1 Production API
"""

import re
import requests
from datetime import datetime
from typing import Tuple, Optional

from src.utils.state_manager import app_state


# API Configuration
API_BASE_URL = "http://localhost:8000"
API_V1_URL = f"{API_BASE_URL}/api/v1"
API_TIMEOUT = 10  # seconds


class AuthService:
    """Handles authentication operations with v1 API integration"""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 6
    
    _access_token: Optional[str] = None
    _refresh_token: Optional[str] = None
    
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
        return True, ""
    
    @staticmethod
    def get_auth_headers() -> dict:
        """Get authorization headers for API requests"""
        if AuthService._access_token:
            return {"Authorization": f"Bearer {AuthService._access_token}"}
        return {}
    
    @staticmethod
    def login(email: str, password: str) -> Tuple[bool, str]:
        """
        Login user via v1 API.
        
        Returns: (success: bool, message: str)
        """
        if not email.strip():
            return False, "Vui lòng nhập email/username!"
        if not password.strip():
            return False, "Vui lòng nhập mật khẩu!"
        
        try:
            response = requests.post(
                f"{API_V1_URL}/auth/login",
                json={
                    "email": email,  # API uses 'email' field for login
                    "password": password
                },
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Store tokens
                AuthService._access_token = data.get("access_token")
                AuthService._refresh_token = data.get("refresh_token")
                
                # Store user info
                user = data.get("user", {})
                app_state.user_info["name"] = user.get("username", "User")
                app_state.user_info["email"] = user.get("email", "")
                app_state.user_info["user_id"] = user.get("user_id")
                app_state.user_info["last_login"] = datetime.now().isoformat()
                app_state.user_info["password"] = ""
                
                # Save state
                app_state.save_state()
                
                return True, "Đăng nhập thành công!"
            
            elif response.status_code == 401:
                error = response.json().get("detail", "Thông tin đăng nhập không chính xác!")
                return False, error
            else:
                return False, "Lỗi đăng nhập. Vui lòng thử lại."
                
        except requests.exceptions.ConnectionError:
            return False, "Không thể kết nối đến server!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    @staticmethod
    def signup(name: str, email: str, password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Register new user via v1 API.
        
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
        
        # Validate password strength
        is_valid, error_msg = AuthService.is_valid_password(password)
        if not is_valid:
            return False, error_msg
        
        if password != confirm_password:
            return False, "Mật khẩu không khớp!"
        
        try:
            response = requests.post(
                f"{API_V1_URL}/auth/register",
                json={
                    "username": name,
                    "email": email,
                    "password": password
                },
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Store tokens
                AuthService._access_token = data.get("access_token")
                AuthService._refresh_token = data.get("refresh_token")
                
                # Store user info
                user = data.get("user", {})
                app_state.user_info["name"] = user.get("username", name)
                app_state.user_info["email"] = user.get("email", email)
                app_state.user_info["user_id"] = user.get("user_id")
                app_state.user_info["last_login"] = datetime.now().isoformat()
                app_state.user_info["password"] = ""
                
                # Save state
                app_state.save_state()
                
                return True, "Đăng ký thành công!"
            
            elif response.status_code == 400:
                error = response.json().get("detail", "Email đã tồn tại!")
                return False, error
            else:
                return False, "Lỗi đăng ký. Vui lòng thử lại."
                
        except requests.exceptions.ConnectionError:
            return False, "Không thể kết nối đến server!"
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
    
    @staticmethod
    def refresh_token() -> bool:
        """Refresh access token using refresh token"""
        if not AuthService._refresh_token:
            return False
        
        try:
            response = requests.post(
                f"{API_V1_URL}/auth/refresh",
                json={"refresh_token": AuthService._refresh_token},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                AuthService._access_token = data.get("access_token")
                AuthService._refresh_token = data.get("refresh_token")
                return True
        except:
            pass
        
        return False
    
    @staticmethod
    def logout() -> Tuple[bool, str]:
        """Logout user and clear tokens"""
        AuthService._access_token = None
        AuthService._refresh_token = None
        
        app_state.save_state()  # Save preferences before logout
        app_state.reset_user()
        app_state.reset_chat()
        return True, "Đã đăng xuất!"
    
    @staticmethod
    def is_logged_in() -> bool:
        """Check if user is logged in"""
        return app_state.user_info.get("user_id") is not None
    
    @staticmethod
    def get_current_user() -> Optional[dict]:
        """Get current logged in user info from state or API"""
        if AuthService.is_logged_in():
            return {
                "user_id": app_state.user_info.get("user_id"),
                "name": app_state.user_info.get("name"),
                "email": app_state.user_info.get("email"),
                "last_login": app_state.user_info.get("last_login")
            }
        
        # Try to get from API if token exists
        if AuthService._access_token:
            try:
                response = requests.get(
                    f"{API_V1_URL}/auth/me",
                    headers=AuthService.get_auth_headers(),
                    timeout=API_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    app_state.user_info["user_id"] = data.get("user_id")
                    app_state.user_info["name"] = data.get("username")
                    app_state.user_info["email"] = data.get("email")
                    return data
            except:
                pass
        
        return None


# Singleton instance
auth_service = AuthService()

