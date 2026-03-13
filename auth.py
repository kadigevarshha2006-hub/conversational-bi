import bcrypt
from database import create_user, get_user

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
        raise ValueError("Username and password are required")
        
    hashed = hash_password(password)
    user_id = create_user(username, hashed)
    
    if not user_id:
        raise ValueError("Username already exists")
    
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
