#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for the EVE Trading Platform.

This script generates a cryptographically secure random key
using Python's secrets module (recommended for security purposes).

Usage:
    python generate_secret_key.py
"""

import secrets

def generate_secret_key(length: int = 32) -> str:
    """
    Generate a secure random secret key.
    
    Args:
        length: Number of bytes for the key (default 32)
        
    Returns:
        Hex-encoded secret key string
    """
    return secrets.token_hex(length)


if __name__ == "__main__":
    secret_key = generate_secret_key()
    print(f"Generated SECRET_KEY:\n{secret_key}")
    print(f"\nLength: {len(secret_key)} characters")
    print("\nAdd this to your .env file:")
    print(f"SECRET_KEY={secret_key}")
