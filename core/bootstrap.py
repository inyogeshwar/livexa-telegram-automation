import sys
import os
from encryption import security
from dotenv import set_key

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/livexa.env')

def bootstrap_token(token_plain):
    """
    Encrypts the provided token and writes it to livexa.env.
    """
    if not token_plain:
        print("Error: No token provided.")
        sys.exit(1)

    print(f"Encrypting token...")
    token_enc = security.encrypt(token_plain)
    
    # Create env file if not exists
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as f:
            f.write("# Livexa Configuration\n")

    # Update .env securely
    # We use python-dotenv set_key if available, or manual write
    # Since set_key handles quoting and existing keys, we try to use it 
    # OR simpler: manual write since we own the file structure.
    
    try:
        # Simple manual update to avoid python-dotenv dependency complexity in install script
        # Read existing lines
        lines = []
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                lines = f.readlines()
        
        new_lines = []
        found = False
        for line in lines:
            if line.startswith("LIVEXA_BOT_TOKEN_ENC="):
                new_lines.append(f"LIVEXA_BOT_TOKEN_ENC={token_enc}\n")
                found = True
            elif line.startswith("LIVEXA_BOT_TOKEN_PLAIN="):
                # Remove plain token if present
                continue
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f"LIVEXA_BOT_TOKEN_ENC={token_enc}\n")
            
        with open(CONFIG_PATH, 'w') as f:
            f.writelines(new_lines)
            
        print("✅ Token encrypted and stored in config/livexa.env")
        
    except Exception as e:
        print(f"❌ Failed to write config: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 bootstrap.py <TOKEN>")
        sys.exit(1)
    
    bootstrap_token(sys.argv[1])
