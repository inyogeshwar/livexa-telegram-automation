from cryptography.fernet import Fernet
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../config/livexa.env'))

class LivexaSecurity:
    """
    Handles AES-256 encryption and decryption for sensitive data.
    """
    def __init__(self):
        self.key = os.getenv('LIVEXA_SECRET_KEY')
        if not self.key:
            print("CRITICAL: LIVEXA_SECRET_KEY not found in config/livexa.env")
            print("Please run install.sh or generate a key.")
            sys.exit(1)
        try:
            self.cipher = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
        except Exception as e:
            print(f"Error initializing encryption: {e}")
            sys.exit(1)

    def encrypt(self, data: str) -> str:
        """Encrypts a string."""
        if not data:
            return ""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        """Decrypts a token."""
        if not token:
            return ""
        try:
            return self.cipher.decrypt(token.encode()).decode()
        except Exception as e:
            print(f"Decryption failed: {e}")
            return None

# Singleton instance
security = LivexaSecurity()
