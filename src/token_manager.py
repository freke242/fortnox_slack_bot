"""
Token Manager - Handles Fortnox token storage
Supports both PostgreSQL (Railway production/staging) and file-based (local) storage

Storage Strategy:
- Production (Railway main): PostgreSQL with read/write access (manages token refresh)
- Staging (Railway staging): PostgreSQL with read-only access (consumes latest tokens)
- Local development: File-based storage with optional PostgreSQL read-only sync
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
USE_DATABASE = DATABASE_URL is not None

# Read-only mode - staging/local should not write tokens
TOKEN_STORAGE_READONLY = os.getenv('TOKEN_STORAGE_READONLY', 'false').lower() == 'true'

# File configuration (fallback for local development)
TOKEN_FILE = os.getenv('TOKEN_FILE', 'fortnox_tokens.json')

# Import PostgreSQL driver only if database is configured
if USE_DATABASE:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        logger.info("PostgreSQL driver loaded successfully")
    except ImportError:
        logger.warning("psycopg2 not installed, falling back to file storage")
        USE_DATABASE = False


@contextmanager
def get_db_connection():
    """Context manager for database connections with automatic commit/rollback"""
    if not USE_DATABASE:
        raise RuntimeError("Database not configured")
    
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


class TokenManager:
    """
    Manages Fortnox OAuth tokens with support for both database and file storage
    
    Storage Strategy:
    - Railway production (main branch): PostgreSQL database (read/write)
    - Railway staging (staging branch): PostgreSQL database (read-only)
    - Local development: JSON file with optional database sync
    
    Read-Only Mode:
    When TOKEN_STORAGE_READONLY=true, save_tokens() becomes a no-op.
    This prevents staging/local from writing tokens - only production manages refresh.
    
    Thread Safety:
    - Database: PostgreSQL handles concurrency
    - File: Uses threading.Lock for file operations
    """
    
    def __init__(self):
        self.file_lock = threading.Lock()
        self.storage_type = "database" if USE_DATABASE else "file"
        self.readonly = TOKEN_STORAGE_READONLY
        
        storage_mode = "read-only" if self.readonly else "read/write"
        logger.info(f"TokenManager initialized: {self.storage_type} storage ({storage_mode})")
        
        if USE_DATABASE:
            self._init_database()
        elif not USE_DATABASE:
            # Local file storage setup
            volume_path = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
            if volume_path:
                self.token_file = Path(volume_path) / TOKEN_FILE
                logger.info(f"Using Railway volume for tokens: {self.token_file}")
            else:
                self.token_file = Path(TOKEN_FILE)
                logger.info(f"Using local file for tokens: {self.token_file}")
    
    def _init_database(self):
        """Create tokens table if it doesn't exist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Create table with single-row constraint
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS fortnox_tokens (
                            id INTEGER PRIMARY KEY DEFAULT 1,
                            access_token TEXT NOT NULL,
                            refresh_token TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT single_row CHECK (id = 1)
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_tokens_updated 
                        ON fortnox_tokens(updated_at DESC);
                    """)
            logger.info("✅ Database table initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def load_tokens(self) -> Optional[Dict[str, str]]:
        """
        Load tokens from storage
        
        Returns:
            dict with 'access_token' and 'refresh_token' keys, or None if not found
        """
        if USE_DATABASE:
            return self._read_from_db()
        else:
            return self._read_from_file()
    
    def _read_from_db(self) -> Optional[Dict[str, str]]:
        """Read tokens from PostgreSQL database"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT access_token, refresh_token, updated_at
                        FROM fortnox_tokens 
                        WHERE id = 1
                    """)
                    row = cur.fetchone()
                    
                    if row:
                        logger.info(f"✅ Tokens read from database (updated: {row['updated_at']})")
                        return {
                            'access_token': row['access_token'],
                            'refresh_token': row['refresh_token']
                        }
                    else:
                        logger.warning("No tokens found in database")
                        return None
        except Exception as e:
            logger.error(f"Failed to read tokens from database: {e}")
            return None
    
    def _read_from_file(self) -> Optional[Dict[str, str]]:
        """Read tokens from JSON file (local development)"""
        with self.file_lock:
            try:
                if not self.token_file.exists():
                    logger.warning(f"Token file not found: {self.token_file}")
                    return None
                
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
                
                # Validate token structure
                if 'access_token' not in tokens or 'refresh_token' not in tokens:
                    logger.warning("Token file missing required keys")
                    return None
                
                logger.info(f"✅ Tokens read from file: {self.token_file}")
                return tokens
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse token file: {e}")
                return None
            except Exception as e:
                logger.error(f"Failed to read tokens from file: {e}")
                return None
    
    def save_tokens(self, access_token: str, refresh_token: str) -> bool:
        """
        Write tokens to storage
        
        In read-only mode, this becomes a no-op to prevent staging/local from
        overwriting production's tokens.
        
        Args:
            access_token: Fortnox access token
            refresh_token: Fortnox refresh token
            
        Returns:
            True if successful (or skipped in read-only mode), False otherwise
        """
        if self.readonly:
            logger.warning("⚠️  Token storage is READ-ONLY - save_tokens() skipped")
            logger.warning("   Only production environment should refresh tokens")
            return True  # Return True to avoid breaking token refresh flow
        
        if USE_DATABASE:
            return self._write_to_db(access_token, refresh_token)
        else:
            return self._write_to_file(access_token, refresh_token)
    
    def _write_to_db(self, access_token: str, refresh_token: str) -> bool:
        """Write tokens to PostgreSQL database"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO fortnox_tokens (id, access_token, refresh_token)
                        VALUES (1, %s, %s)
                        ON CONFLICT (id) 
                        DO UPDATE SET 
                            access_token = EXCLUDED.access_token,
                            refresh_token = EXCLUDED.refresh_token,
                            updated_at = CURRENT_TIMESTAMP
                    """, (access_token, refresh_token))
            
            logger.info("✅ Tokens written to database successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to write tokens to database: {e}")
            return False
    
    def _write_to_file(self, access_token: str, refresh_token: str) -> bool:
        """Write tokens to JSON file (local development)"""
        with self.file_lock:
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
                
                logger.info(f"✅ Tokens written to file: {self.token_file}")
                return True
            except Exception as e:
                logger.error(f"Failed to write tokens to file: {e}")
                return False
    
    def initialize_from_env(self) -> bool:
        """
        Initialize token storage from environment variables if it doesn't exist
        
        For database: Seeds the database with initial tokens
        For file: Creates token file from env vars
        
        Returns:
            True if successful or storage already exists
        """
        # Check if tokens already exist
        existing_tokens = self.load_tokens()
        if existing_tokens:
            logger.info("Tokens already exist in storage, skipping initialization from env")
            return True
        
        # Get tokens from environment
        access_token = os.environ.get("FORTNOX_ACCESS_TOKEN")
        refresh_token = os.environ.get("FORTNOX_REFRESH_TOKEN")
        
        if not access_token or not refresh_token:
            logger.warning("Missing FORTNOX_ACCESS_TOKEN or FORTNOX_REFRESH_TOKEN in environment")
            logger.warning("Cannot initialize storage from environment variables")
            return False
        
        if self.readonly:
            logger.warning("⚠️  Cannot initialize tokens in read-only mode")
            logger.warning("   Tokens must be initialized by production environment first")
            return False
        
        logger.info(f"Initializing {self.storage_type} storage from environment variables...")
        return self.save_tokens(access_token, refresh_token)
    
    def get_refresh_token(self) -> Optional[str]:
        """Get the current refresh token"""
        tokens = self.load_tokens()
        return tokens.get('refresh_token') if tokens else None
    
    def get_access_token(self) -> Optional[str]:
        """Get the current access token"""
        tokens = self.load_tokens()
        return tokens.get('access_token') if tokens else None
    
    def get_storage_info(self) -> Dict[str, str]:
        """Get information about current storage configuration"""
        info = {
            'storage_type': self.storage_type,
            'readonly': str(self.readonly),
            'environment': os.getenv('ENVIRONMENT', 'unknown')
        }
        
        if USE_DATABASE:
            # Mask sensitive parts of DATABASE_URL
            db_url = DATABASE_URL[:30] + '...' if DATABASE_URL and len(DATABASE_URL) > 30 else 'None'
            info['database_url'] = db_url
        else:
            info['token_file'] = str(self.token_file)
        
        return info
