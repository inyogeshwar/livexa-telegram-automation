import sys
import os
import json
from cryptography.fernet import Fernet

CONFIG_DIR = os.path.join(os.path.dirname(__file__), '../config')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'livexa.env')
STORAGE_DIR = os.path.join(os.path.dirname(__file__), '../storage')
ADMINS_PATH = os.path.join(STORAGE_DIR, 'admins.json')

def bootstrap_system(token_plain, admin_id):
    """
    1. Generates Key & Encrypts Token.
    2. Writes livexa.env.
    3. Writes storage/admins.json directly.
    """
    if not token_plain or not admin_id:
        print("❌ Error: Missing Token or Admin ID.")
        sys.exit(1)

    print(f"🔐 Securing Credentials...")
    
    # 1. Encrypt Token
    key = Fernet.generate_key()
    cipher = Fernet(key)
    token_enc = cipher.encrypt(token_plain.encode()).decode()

    # 2. Write Config
    config_content = (
        f"LIVEXA_SECRET_KEY={key.decode()}\n"
        f"LIVEXA_BOT_TOKEN_ENC={token_enc}\n"
    )
    
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            f.write(config_content)
        os.chmod(CONFIG_PATH, 0o644) # Make readable for now to avoid permission hell

        # 3. Write Admin
        os.makedirs(STORAGE_DIR, exist_ok=True)
        admin_data = {"admins": [int(admin_id)]}
        with open(ADMINS_PATH, 'w') as f:
            json.dump(admin_data, f)
        os.chmod(ADMINS_PATH, 0o666) # Ensure readable by everyone for now

        print(f"✅ Configured. Admin ID {admin_id} authorized.")

    except Exception as e:
        print(f"❌ Bootstrap Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 bootstrap.py <TOKEN> <ADMIN_ID>")
        sys.exit(1)
    
    bootstrap_system(sys.argv[1], sys.argv[2])
