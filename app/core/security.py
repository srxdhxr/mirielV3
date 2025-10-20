"""
Security utilities for password hashing and validation
"""
import hashlib
import secrets
import re


def hash_password(password: str) -> tuple[bytes, bytes]:
    """
    Hash a password with a random salt using SHA-256
    
    Returns:
        tuple: (password_hash, password_salt)
    """
    # Generate random salt (32 bytes)
    salt = secrets.token_bytes(32)
    
    # Hash password with salt
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=100000  # Industry standard
    )
    
    return password_hash, salt


def verify_password(password: str, salt: bytes, stored_hash: bytes) -> bool:
    """
    Verify a password against stored hash and salt
    
    Args:
        password: Plain text password to verify
        salt: The stored salt
        stored_hash: The stored password hash
        
    Returns:
        bool: True if password matches, False otherwise
    """
    # Hash the provided password with the same salt
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=100000
    )
    
    # Compare hashes (constant-time comparison)
    return secrets.compare_digest(password_hash, stored_hash)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength
    
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, ""


def validate_email(email: str) -> bool:
    """
    Basic email validation
    
    Returns:
        bool: True if email format is valid
    """
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email))

