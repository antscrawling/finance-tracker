from hashlib import pbkdf2_hmac
import os
from models import User, Session

class PasswordAuth:
    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> tuple[str, bytes]:
        """Hash a password using PBKDF2 with SHA256"""
        if salt is None:
            salt = os.urandom(16)
        hash_bytes = pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return hash_bytes.hex(), salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: bytes) -> bool:
        """Verify a password against its hash"""
        hash_attempt, _ = PasswordAuth.hash_password(password, salt)
        return stored_hash == hash_attempt

    @staticmethod
    def authenticate_user(username: str, password: str) -> tuple[bool, str, User]:
        """Authenticate a user with username and password"""
        try:
            session = Session()
            user = session.query(User).filter_by(username=username).first()
            
            if not user:
                return False, "User not found", None
                
            if not PasswordAuth.verify_password(password, user.password_hash, user.salt):
                return False, "Invalid password", None
                
            return True, "Authentication successful", user
            
        except Exception as e:
            return False, f"Authentication error: {str(e)}", None
        finally:
            session.close()