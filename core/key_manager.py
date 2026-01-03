import os
import json
from typing import Dict, List, Optional
from encryption import security

STORAGE_ROOT = os.path.join(os.path.dirname(__file__), '../storage')

class KeyManager:
    """
    Manages encrypted stream keys.
    Structure: storage/<chat_id>/keys.json
    """
    def __init__(self, root_path=STORAGE_ROOT):
        self.root = root_path
        if not os.path.exists(self.root):
            os.makedirs(self.root)

    def _get_key_file(self, chat_id: int) -> str:
        path = os.path.join(self.root, str(chat_id))
        if not os.path.exists(path):
            os.makedirs(path)
        return os.path.join(path, 'keys.json')

    def add_key(self, chat_id: int, alias: str, key_value: str):
        keys = self._load_keys(chat_id)
        # Encrypt before storage
        encrypted_val = security.encrypt(key_value)
        keys[alias] = encrypted_val
        self._save_keys(chat_id, keys)

    def delete_key(self, chat_id: int, alias: str) -> bool:
        keys = self._load_keys(chat_id)
        if alias in keys:
            del keys[alias]
            self._save_keys(chat_id, keys)
            return True
        return False

    def get_key(self, chat_id: int, alias: str) -> Optional[str]:
        keys = self._load_keys(chat_id)
        if alias in keys:
            # Decrypt on retrieval
            return security.decrypt(keys[alias])
        return None

    def list_keys(self, chat_id: int) -> List[str]:
        keys = self._load_keys(chat_id)
        return list(keys.keys())

    def _load_keys(self, chat_id: int) -> Dict[str, str]:
        path = self._get_key_file(chat_id)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_keys(self, chat_id: int, data: Dict[str, str]):
        path = self._get_key_file(chat_id)
        with open(path, 'w') as f:
            json.dump(data, f)

key_manager = KeyManager()
