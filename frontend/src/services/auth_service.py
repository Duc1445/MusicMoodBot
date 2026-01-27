"""
Authentication service for MusicMoodBot
Handles user login, signup, and session management
"""

import re

from backend.database import add_user, get_user
from src.utils.state_manager import app_state


class AuthService:
    """Handles authentication operations"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_password(password: str) -> bool:
        """Validate password (at least 6 characters)"""
        return len(password.strip()) >= 6
    
    @staticmethod
    def login(email: str, password: str) -> tuple[bool, str]:
        """
        Login user
        Returns: (success: bool, message: str)
        """
        if not email.strip():
            return False, "Vui lòng nhập email/username!"
        if not password.strip():
            return False, "Vui lòng nhập mật khẩu!"
        
        # Check user in database
        user = get_user(email)
        if not user or user["password"] != password:
            return False, "Email/username hoặc mật khẩu không chính xác!"
        
        # Store user in state
        app_state.user_info["name"] = user.get("username", "User")
        app_state.user_info["email"] = user.get("email", "")
        app_state.user_info["user_id"] = user.get("user_id", None)
        app_state.user_info["password"] = user.get("password", "")
        
        return True, "Login successful!"
    
    @staticmethod
    def signup(name: str, email: str, password: str, confirm_password: str) -> tuple[bool, str]:
        """
        Register new user
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
        if not AuthService.is_valid_password(password):
            return False, "Mật khẩu phải có ít nhất 6 ký tự!"
        if password != confirm_password:
            return False, "Mật khẩu không khớp!"
        
        # Add user to database
        user_id = add_user(name, email, password)
        if not user_id:
            return False, "Email đã tồn tại! Vui lòng dùng email khác."
        # Store user in state
        app_state.user_info["name"] = name
        app_state.user_info["email"] = email
        app_state.user_info["user_id"] = user_id
        app_state.user_info["password"] = password
        
        return True, "Signup successful!"
    
    @staticmethod
    def logout():
        """Logout user"""
        app_state.reset_user()
        app_state.reset_chat()
        return True, "Logged out"


# Singleton instance
auth_service = AuthService()
