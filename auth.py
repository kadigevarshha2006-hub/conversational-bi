import bcrypt
import re
from database import create_user, get_user

def validate_email_format(email):
    """Basic regex check for an email format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(pattern, email):
        raise ValueError("Invalid email format. Please provide a valid company email (e.g., user@company.com).")

def validate_password_strength(password):
    """Check if password is at least 8 characters and contains a number."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one number.")

def hash_password(password):
    """Hash a password for storing."""
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return pw_hash.decode('utf-8')

def verify_password(password, hashed_password):
    """Verify a stored password against one provided by user"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(username, password):
    """Registers a new user and returns their user ID. Raises Exception if username exists."""
    if not username or not password:
        raise ValueError("Email and password are required.")
        
    validate_email_format(username)
    validate_password_strength(password)
        
    hashed = hash_password(password)
    user_id = create_user(username, hashed)
    
    if not user_id:
        raise ValueError("An account with this email already exists.")
    
    return user_id

def authenticate_user(username, password):
    """Authenticates a user and returns their user ID if successful, False otherwise."""
    user = get_user(username)
    if not user:
        return False
        
    if verify_password(password, user['password_hash']):
        return user['id']
    else:
        return False
