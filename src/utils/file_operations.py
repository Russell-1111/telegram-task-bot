"""
File Operations Module

This module provides secure file operation utilities for state persistence.
Includes atomic writes, secure permissions, backup rotation, and JSON handling.

Functions:
    atomic_write(): Write file atomically using temp file + rename
    set_secure_permissions(): Set restrictive file permissions (0600/user-only)
    rotate_backups(): Rotate backup files maintaining retention limit
    safe_json_load(): Load JSON file with error handling
    safe_json_save(): Save JSON file with atomic write and error handling

Usage:
    from utils.file_operations import atomic_write, safe_json_save
    
    # Atomic write
    atomic_write("data/state.json", '{"key": "value"}')
    
    # JSON operations
    safe_json_save("data/state.json", {"key": "value"})
    data = safe_json_load("data/state.json")
"""

import os
import json
import shutil
import logging
import platform
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def atomic_write(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Write content to file atomically using temp file + rename pattern.
    
    This prevents corruption from interrupted writes by:
    1. Writing to a temporary file first
    2. Verifying the write succeeded
    3. Atomically renaming temp file to target (replaces existing file)
    
    Args:
        filepath (str): Target file path
        content (str): Content to write
        encoding (str): File encoding (default: utf-8)
        
    Returns:
        bool: True if write succeeded, False otherwise
        
    Raises:
        Exception: If write operation fails
        
    Example:
        >>> atomic_write("data/state.json", '{"key": "value"}')
        True
    """
    filepath_obj = Path(filepath)
    temp_file = filepath_obj.with_suffix(filepath_obj.suffix + '.tmp')
    
    try:
        # Ensure parent directory exists
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file
        temp_file.write_text(content, encoding=encoding)
        
        # Set secure permissions on temp file before rename
        set_secure_permissions(str(temp_file))
        
        # Atomic rename (replaces existing file)
        temp_file.replace(filepath_obj)
        
        logger.debug(
            f"Atomic write succeeded: {filepath} "
            f"({len(content)} chars)"
        )
        return True
        
    except Exception as e:
        logger.error(f"Atomic write failed for {filepath}: {e}")
        # Clean up temp file if it exists
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temp file {temp_file}: {cleanup_error}")
        raise


def set_secure_permissions(filepath: str) -> bool:
    """
    Set restrictive file permissions to protect sensitive data.
    
    - Unix/Linux: chmod 600 (owner read/write only)
    - Windows: Set ACL to restrict access to current user
    
    Args:
        filepath (str): Path to file to secure
        
    Returns:
        bool: True if permissions set successfully, False otherwise
        
    Example:
        >>> set_secure_permissions("data/tokens.enc")
        True
    """
    try:
        filepath_obj = Path(filepath)
        
        if not filepath_obj.exists():
            logger.warning(f"Cannot set permissions: file does not exist: {filepath}")
            return False
        
        system = platform.system()
        
        if system in ('Linux', 'Darwin'):  # Unix-like systems
            # chmod 600 (owner read/write only)
            os.chmod(filepath, 0o600)
            logger.debug(f"Set Unix permissions 0600 on {filepath}")
            return True
            
        elif system == 'Windows':
            # Windows: Use icacls to restrict to current user
            # This is a simplified approach; production may need more robust ACL handling
            try:
                import subprocess
                username = os.getenv('USERNAME')
                
                # Remove all permissions
                subprocess.run(
                    ['icacls', filepath, '/inheritance:r'],
                    capture_output=True,
                    check=True,
                    timeout=5
                )
                
                # Grant full control to current user only
                subprocess.run(
                    ['icacls', filepath, f'/grant:r', f'{username}:F'],
                    capture_output=True,
                    check=True,
                    timeout=5
                )
                
                logger.debug(f"Set Windows ACL for user {username} on {filepath}")
                return True
                
            except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
                logger.warning(f"Failed to set Windows ACL on {filepath}: {e}")
                # Fallback: at least make it non-readable by others using basic attributes
                # Note: This is not as secure as proper ACLs
                os.chmod(filepath, 0o600)
                return False
        else:
            logger.warning(f"Unsupported platform for permission setting: {system}")
            return False
            
    except Exception as e:
        logger.warning(f"Failed to set secure permissions on {filepath}: {e}")
        return False


def rotate_backups(filepath: str, retention: int = 3) -> bool:
    """
    Rotate backup files maintaining the specified retention count.
    
    Before overwriting a file, backs it up and rotates existing backups:
    - file.ext -> file.ext.1
    - file.ext.1 -> file.ext.2
    - file.ext.2 -> file.ext.3
    - file.ext.3 -> deleted (if retention=3)
    
    Args:
        filepath (str): Path to the file to backup
        retention (int): Number of backups to keep (default: 3)
        
    Returns:
        bool: True if rotation succeeded, False if file doesn't exist
        
    Example:
        >>> rotate_backups("data/tokens.enc", retention=3)
        True
    """
    try:
        filepath_obj = Path(filepath)
        
        if not filepath_obj.exists():
            logger.debug(f"No file to backup: {filepath}")
            return False
        
        # Ensure backups directory exists
        backup_dir = filepath_obj.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        filename = filepath_obj.name
        
        # Rotate existing backups (oldest first)
        for i in range(retention - 1, 0, -1):
            old_backup = backup_dir / f"{filename}.{i}"
            new_backup = backup_dir / f"{filename}.{i + 1}"
            
            if old_backup.exists():
                if i + 1 > retention:
                    # Delete if exceeds retention
                    old_backup.unlink()
                    logger.debug(f"Deleted old backup: {old_backup}")
                else:
                    # Rotate to next number
                    old_backup.replace(new_backup)
                    logger.debug(f"Rotated backup: {old_backup} -> {new_backup}")
        
        # Create new backup from current file
        current_backup = backup_dir / f"{filename}.1"
        shutil.copy2(filepath_obj, current_backup)
        set_secure_permissions(str(current_backup))
        
        logger.info(
            f"Backup created: {filepath} -> {current_backup} "
            f"(retention: {retention})"
        )
        return True
        
    except Exception as e:
        logger.error(f"Backup rotation failed for {filepath}: {e}")
        return False


def safe_json_load(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON file with comprehensive error handling.
    
    Handles:
    - Missing file (returns None)
    - JSON parse errors (logs error, backs up corrupted file, returns None)
    - Permission errors (logs error, returns None)
    
    Args:
        filepath (str): Path to JSON file
        
    Returns:
        dict or None: Parsed JSON data, or None if load failed
        
    Example:
        >>> data = safe_json_load("data/state.json")
        >>> if data:
        ...     print(f"Loaded {len(data)} keys")
    """
    try:
        filepath_obj = Path(filepath)
        
        if not filepath_obj.exists():
            logger.debug(f"JSON file does not exist: {filepath}")
            return None
        
        with open(filepath_obj, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.debug(f"Loaded JSON file: {filepath} ({filepath_obj.stat().st_size} bytes)")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(
            f"JSON parse error in {filepath} at line {e.lineno}, column {e.colno}: {e.msg}"
        )
        
        # Backup corrupted file
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupted_backup = filepath_obj.with_suffix(f".corrupted.{timestamp}.json")
            shutil.copy2(filepath_obj, corrupted_backup)
            logger.info(f"Backed up corrupted file to: {corrupted_backup}")
        except Exception as backup_error:
            logger.warning(f"Failed to backup corrupted file: {backup_error}")
        
        return None
        
    except PermissionError as e:
        logger.error(f"Permission denied reading {filepath}: {e}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to load JSON from {filepath}: {e}")
        return None


def safe_json_save(filepath: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    Save data to JSON file with atomic write and error handling.
    
    Features:
    - Atomic write (temp file + rename)
    - Backup rotation before overwriting
    - Secure permissions
    - Pretty-printed JSON for readability
    
    Args:
        filepath (str): Target file path
        data (dict): Data to serialize to JSON
        indent (int): JSON indentation (default: 2 spaces)
        
    Returns:
        bool: True if save succeeded, False otherwise
        
    Example:
        >>> safe_json_save("data/state.json", {"users": {"123": {...}}})
        True
    """
    try:
        # Rotate existing backups
        rotate_backups(filepath)
        
        # Serialize to JSON
        json_content = json.dumps(data, indent=indent, ensure_ascii=False)
        
        # Atomic write
        atomic_write(filepath, json_content)
        
        logger.info(
            f"Saved JSON file: {filepath} "
            f"({len(json_content)} chars, {len(data)} root keys)"
        )
        return True
        
    except Exception as e:
        logger.error(f"Failed to save JSON to {filepath}: {e}")
        return False


def ensure_directory(dirpath: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dirpath (str): Directory path to ensure
        
    Returns:
        bool: True if directory exists or was created, False on error
        
    Example:
        >>> ensure_directory("data/backups")
        True
    """
    try:
        Path(dirpath).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {dirpath}: {e}")
        return False


def get_file_age_seconds(filepath: str) -> Optional[float]:
    """
    Get the age of a file in seconds since last modification.
    
    Args:
        filepath (str): Path to file
        
    Returns:
        float or None: Age in seconds, or None if file doesn't exist
        
    Example:
        >>> age = get_file_age_seconds("data/state.json")
        >>> if age and age > 300:
        ...     print("File is older than 5 minutes")
    """
    try:
        filepath_obj = Path(filepath)
        if not filepath_obj.exists():
            return None
        
        mtime = filepath_obj.stat().st_mtime
        age = datetime.now().timestamp() - mtime
        return age
        
    except Exception as e:
        logger.warning(f"Failed to get file age for {filepath}: {e}")
        return None
