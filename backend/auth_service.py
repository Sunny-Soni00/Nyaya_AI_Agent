import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict

class AuthService:
    def __init__(self):
        self.users_file = 'users.json'
        self.sessions = {}  # In-memory session storage
        
    def _load_users(self):
        """Load users from JSON file"""
        if not os.path.exists(self.users_file):
            return []
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save_users(self, users):
        """Save users to JSON file"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_token(self) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)
    
    def signup(self, email: str, password: str, name: str, role: str) -> Dict:
        """Register a new user"""
        users = self._load_users()
        
        # Check if email already exists
        if any(user['email'] == email for user in users):
            return {
                "success": False,
                "error": "Email already registered"
            }
        
        # Validate inputs
        if not email or not password or not name:
            return {
                "success": False,
                "error": "All fields are required"
            }
        
        if len(password) < 6:
            return {
                "success": False,
                "error": "Password must be at least 6 characters"
            }
        
        # Create new user
        new_user = {
            "id": len(users) + 1,
            "email": email,
            "password": self._hash_password(password),
            "name": name,
            "role": role,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        users.append(new_user)
        self._save_users(users)
        
        # Generate session token
        token = self._generate_token()
        self.sessions[token] = {
            "user_id": new_user['id'],
            "email": email,
            "name": name,
            "role": role,
            "expires_at": datetime.now() + timedelta(days=7)
        }
        
        return {
            "success": True,
            "message": "Account created successfully",
            "token": token,
            "user": {
                "id": new_user['id'],
                "email": email,
                "name": name,
                "role": role,
                "created_at": new_user['created_at']
            }
        }
    
    def login(self, email: str, password: str) -> Dict:
        """Authenticate user and create session"""
        users = self._load_users()
        
        # Find user
        user = next((u for u in users if u['email'] == email), None)
        
        if not user:
            return {
                "success": False,
                "error": "Invalid email or password"
            }
        
        # Verify password
        if user['password'] != self._hash_password(password):
            return {
                "success": False,
                "error": "Invalid email or password"
            }
        
        # Generate session token
        token = self._generate_token()
        self.sessions[token] = {
            "user_id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "role": user['role'],
            "expires_at": datetime.now() + timedelta(days=7)
        }
        
        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "name": user['name'],
                "role": user['role'],
                "created_at": user.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            }
        }
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify session token and return user info"""
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        
        # Check if session expired
        if datetime.now() > session['expires_at']:
            del self.sessions[token]
            return None
        
        return {
            "user_id": session['user_id'],
            "email": session['email'],
            "name": session['name'],
            "role": session['role']
        }
    
    def logout(self, token: str) -> bool:
        """Remove session token"""
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False

# Create global auth service instance
auth_service = AuthService()
