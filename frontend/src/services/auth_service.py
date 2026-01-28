"""
Authentication service for MusicMoodBot
Handles user login, signup, and session management
With secure password hashing
"""

import re
import hashlib
import secrets
from datetime import datetime
from typing import Tuple, Optional

from backend.src.database.database import add_user, get_user
from src.utils.state_manager import app_state


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
    
    # Combine password and salt, then hash
    salted = f"{password}{salt}"
    hashed = hashlib.sha256(salted.encode('utf-8')).hexdigest()
    
    return hashed, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """
    Verify password against stored hash.
    
    Args:
        password: Plain text password to verify
        stored_hash: Stored password hash
        salt: Salt used for hashing
        
    Returns:
        True if password matches
    """
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


class AuthService:
    """Handles authentication operations with secure password handling"""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 6
    REQUIRE_UPPERCASE = False
    REQUIRE_LOWERCASE = False
    REQUIRE_DIGIT = False
    REQUIRE_SPECIAL = False
    
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
    
    @staticmethod
    def login(email: str, password: str) -> Tuple[bool, str]:
        """
        Login user with password verification.
        
        Returns: (success: bool, message: str)
        """
        if not email.strip():
            return False, "Vui lòng nhập email/username!"
        if not password.strip():
            return False, "Vui lòng nhập mật khẩu!"
        
        # Check user in database
        user = get_user(email)
        if not user:
            return False, "Email/username không tồn tại!"
        
        # Database column is password_hash, not password
        stored_password = user.get("password_hash", user.get("password", ""))
        
        # Check if password is hashed (contains salt separator)
        if ":" in stored_password:
            # New hashed format: "hash:salt"
            stored_hash, salt = stored_password.split(":", 1)
            if not verify_password(password, stored_hash, salt):
                return False, "Mật khẩu không chính xác!"
        else:
            # Legacy plain text password (for backward compatibility)
            if stored_password != password:
                return False, "Mật khẩu không chính xác!"
            # Migrate to hashed password
            AuthService._migrate_password(email, password)
        
        # Store user in state
        app_state.user_info["name"] = user.get("username", "User")
        app_state.user_info["email"] = user.get("email", "")
        app_state.user_info["user_id"] = user.get("user_id", None)
        app_state.user_info["last_login"] = datetime.now().isoformat()
        # Don't store password in state for security
        app_state.user_info["password"] = ""
        
        # Save state
        app_state.save_state()
        
        return True, "Đăng nhập thành công!"
    
    @staticmethod
    def _migrate_password(email: str, plain_password: str):
        """Migrate plain text password to hashed format"""
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
    
    @staticmethod
    def signup(name: str, email: str, password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Register new user with hashed password.
        
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
        
        # Hash password before storing
        hashed, salt = hash_password(password)
        stored_format = f"{hashed}:{salt}"
        
        # Add user to database with hashed password
        user_id = add_user(name, email, stored_format)
        if not user_id:
            return False, "Email đã tồn tại! Vui lòng dùng email khác."
        
        # Store user in state
        app_state.user_info["name"] = name
        app_state.user_info["email"] = email
        app_state.user_info["user_id"] = user_id
        app_state.user_info["last_login"] = datetime.now().isoformat()
        app_state.user_info["password"] = ""  # Don't store password
        
        # Save state
        app_state.save_state()
        
        return True, "Đăng ký thành công!"
    
    @staticmethod
    def change_password(old_password: str, new_password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Change user password.
        
        Returns: (success: bool, message: str)
        """
        user_id = app_state.user_info.get("user_id")
        if not user_id:
            return False, "Bạn chưa đăng nhập!"
        
        # Get user from database
        email = app_state.user_info.get("email", "")
        user = get_user(email)
        if not user:
            return False, "Không tìm thấy người dùng!"
        
        # Verify old password
        stored_password = user.get("password", "")
        if ":" in stored_password:
            stored_hash, salt = stored_password.split(":", 1)
            if not verify_password(old_password, stored_hash, salt):
                return False, "Mật khẩu cũ không chính xác!"
        else:
            if stored_password != old_password:
                return False, "Mật khẩu cũ không chính xác!"
        
        # Validate new password
        is_valid, error_msg = AuthService.is_valid_password(new_password)
        if not is_valid:
            return False, error_msg
        
        if new_password != confirm_password:
            return False, "Mật khẩu mới không khớp!"
        
        # Hash and update new password
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
        """Logout user and save state"""
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
        """Get current logged in user info"""
        if AuthService.is_logged_in():
            return {
                "user_id": app_state.user_info.get("user_id"),
                "name": app_state.user_info.get("name"),
                "email": app_state.user_info.get("email"),
                "last_login": app_state.user_info.get("last_login")
            }
        return None


# Singleton instance
auth_service = AuthService()
