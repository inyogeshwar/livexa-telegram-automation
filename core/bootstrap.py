import sys
import os
from cryptography.fernet import Fernet
# We avoid local imports that might depend on env vars being present
# to ensure this script runs standalone during install.

CONFIG_DIR = os.path.join(os.path.dirname(__file__), '../config')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'livexa.env')

def bootstrap_system(token_plain):
    """
    Generates a fresh Livexa configuration:
    1. Generates a new AES-256 Secret Key.
    2. Encrypts the provided Bot Token.
    3. Writes the secure config file at config/livexa.env.
    """
    if not token_plain:
        print("❌ Error: No token provided.")
        sys.exit(1)

    print(f"🔐 Securing Credentials...")

    # 1. Generate Master Key
    key = Fernet.generate_key()
    cipher = Fernet(key)
    secret_key_str = key.decode()

    # 2. Encrypt Token
    token_bytes = token_plain.encode()
    token_enc = cipher.encrypt(token_bytes).decode()

    # 3. Generate Config Content
    config_content = (
        "# 🔴 Livexa Production Configuration\n"
        "# AUTO-GENERATED - DO NOT EDIT MANUALLY\n\n"
        f"LIVEXA_SECRET_KEY={secret_key_str}\n"
        f"LIVEXA_BOT_TOKEN_ENC={token_enc}\n"
        f"LIVEXA_ADMIN_IDS=\n"  # Empty initially, handled by Setup Wizard
    )

    # 4. Write File
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            f.write(config_content)
        
        # Set restricted permissions (600)
        os.chmod(CONFIG_PATH, 0o600)
        print("✅ Configuration secured.")
        
    except Exception as e:
        print(f"❌ Failed to write config: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 bootstrap.py <TOKEN>")
        sys.exit(1)
    
    bootstrap_system(sys.argv[1])
