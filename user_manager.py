# user_manager.py - Enhanced User Management Module with JSON storage

import json
import logging
import os
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self, admin_id, max_users, data_file='users_data.json'):
        """Initialize user manager with admin ID, max users limit, and data file path"""
        self.admin_id = str(admin_id)
        self.max_users = max_users
        self.data_file = data_file
        self.users = {}
        self.lock = Lock()  # Thread-safe file operations
        
        # Load existing users from JSON file
        self.load_users()
    
    def load_users(self):
        """Load user data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.users = data.get('users', {})
                    logger.info(f"Loaded {len(self.users)} users from {self.data_file}")
            else:
                logger.info(f"No existing user data file found. Starting fresh.")
                self.users = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {self.data_file}: {e}")
            logger.warning("Starting with empty user database")
            self.users = {}
        except Exception as e:
            logger.error(f"Error loading users from {self.data_file}: {e}")
            self.users = {}
    
    def save_users(self):
        """Save user data to JSON file"""
        try:
            with self.lock:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump({'users': self.users}, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved {len(self.users)} users to {self.data_file}")
        except Exception as e:
            logger.error(f"Error saving users to {self.data_file}: {e}")
    
    def is_authorized(self, user_id):
        """Check if user exists in the system"""
        return str(user_id) in self.users
    
    def is_admin(self, user_id):
        """Check if user is the admin"""
        return str(user_id) == self.admin_id
    
    def can_accept_new_user(self):
        """Check if the bot can accept a new user (under MAX_USERS limit)"""
        return len(self.users) < self.max_users
    
    def add_user(self, user_id, username=None, first_name=None):
        """Add a new user with join timestamp"""
        user_id_str = str(user_id)
        
        if user_id_str in self.users:
            logger.warning(f"User {user_id} already exists")
            return False
        
        if not self.can_accept_new_user():
            logger.warning(f"Cannot add user {user_id}: user limit reached")
            return False
        
        now = datetime.now().isoformat()
        
        self.users[user_id_str] = {
            'user_id': user_id_str,
            'username': username,
            'first_name': first_name or 'Unknown',
            'joined_at': now,
            'total_tokens': 0,
            'last_activity': now
        }
        
        self.save_users()
        logger.info(f"Added new user: {user_id} ({first_name})")
        return True
    
    def update_tokens(self, user_id, tokens_used):
        """Add tokens to user's total token count"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.users:
            logger.warning(f"Cannot update tokens for unknown user: {user_id}")
            return
        
        self.users[user_id_str]['total_tokens'] += tokens_used
        self.save_users()
        logger.debug(f"Updated tokens for user {user_id}: +{tokens_used}")
    
    def update_last_activity(self, user_id):
        """Update user's last activity timestamp"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.users:
            logger.warning(f"Cannot update activity for unknown user: {user_id}")
            return
        
        self.users[user_id_str]['last_activity'] = datetime.now().isoformat()
        self.save_users()
    
    def get_user_count(self):
        """Return current number of registered users"""
        return len(self.users)
    
    def get_all_users(self):
        """Return all user data (for admin stats)"""
        return self.users
    
    def get_user_info(self, user_id):
        """Get information for a specific user"""
        return self.users.get(str(user_id))
