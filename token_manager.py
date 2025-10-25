"""
Token Manager Module

Handles persistent storage of Fortnox OAuth tokens to survive bot restarts
and properly handle refresh token rotation.

On Railway and other cloud platforms, environment variables can't be updated
at runtime, so we store tokens in a JSON file instead.
"""
import json
import os
import logging
from pathlib import Path
from typing import Optional, Dict
from threading import Lock

logger = logging.getLogger(__name__)


class TokenManager:
    """Manages Fortnox OAuth tokens with persistent file storage"""
    
    def __init__(self, token_file: str = "fortnox_tokens.json"):
        """
        Initialize the token manager
        
        Args:
            token_file: Path to the JSON file for storing tokens
        """
        self.token_file = Path(token_file)
        self.lock = Lock()  # Thread-safe access
        
    def load_tokens(self) -> Optional[Dict[str, str]]:
        """
        Load tokens from file
        
        Returns:
            Dictionary with 'access_token' and 'refresh_token', or None if file doesn't exist
        """
        with self.lock:
            if not self.token_file.exists():
                logger.info(f"Token file {self.token_file} does not exist")
                return None
            
            try:
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
                    
                # Validate token structure
                if 'access_token' not in tokens or 'refresh_token' not in tokens:
                    logger.warning("Token file missing required keys")
                    return None
                
                logger.info("✅ Tokens loaded from file")
                return tokens
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse token file: {e}")
                return None
            except Exception as e:
                logger.error(f"Error loading tokens: {e}")
                return None
    
    def save_tokens(self, access_token: str, refresh_token: str) -> bool:
        """
        Save tokens to file
        
        Args:
            access_token: New access token
            refresh_token: New refresh token
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            try:
                tokens = {
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
                
                # Write atomically: write to temp file, then rename
                temp_file = self.token_file.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(tokens, f, indent=2)
                
                # Atomic rename
                temp_file.replace(self.token_file)
                
                logger.info(f"✅ Tokens saved to {self.token_file}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save tokens: {e}")
                return False
    
    def initialize_from_env(self) -> bool:
        """
        Initialize token file from environment variables if it doesn't exist
        
        Returns:
            True if successful, False otherwise
        """
        # Only initialize if file doesn't exist
        if self.token_file.exists():
            logger.info("Token file already exists, skipping initialization from env")
            return True
        
        # Get tokens from environment
        access_token = os.environ.get("FORTNOX_ACCESS_TOKEN")
        refresh_token = os.environ.get("FORTNOX_REFRESH_TOKEN")
        
        if not access_token or not refresh_token:
            logger.warning("Missing FORTNOX_ACCESS_TOKEN or FORTNOX_REFRESH_TOKEN in environment")
            logger.warning("Cannot initialize token file from environment variables")
            return False
        
        logger.info("Initializing token file from environment variables...")
        return self.save_tokens(access_token, refresh_token)
    
    def get_refresh_token(self) -> Optional[str]:
        """
        Get the current refresh token
        
        Returns:
            Refresh token string or None
        """
        tokens = self.load_tokens()
        return tokens.get('refresh_token') if tokens else None
    
    def get_access_token(self) -> Optional[str]:
        """
        Get the current access token
        
        Returns:
            Access token string or None
        """
        tokens = self.load_tokens()
        return tokens.get('access_token') if tokens else None
