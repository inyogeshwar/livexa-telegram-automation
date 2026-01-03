import os
import json
from typing import Dict, List
from encryption import security

STORAGE_ROOT = os.path.join(os.path.dirname(__file__), '../storage')

class BotManager:
    """
    Manages multiple Telegram Bot tokens.
    Storage: storage/bots.json (Encrypted)
    """
    def __init__(self, root_path=STORAGE_ROOT):
        self.root = root_path
        self.file_path = os.path.join(self.root, 'bots.json')
        if not os.path.exists(self.root):
            os.makedirs(self.root)

    def add_bot(self, alias: str, token: str):
        bots = self._load_bots()
        bots[alias] = security.encrypt(token)
        self._save_bots(bots)

    def remove_bot(self, alias: str):
        bots = self._load_bots()
        if alias in bots:
            del bots[alias]
            self._save_bots(bots)

    def list_bots(self) -> List[str]:
        return list(self._load_bots().keys())

    def get_token(self, alias: str) -> str:
        bots = self._load_bots()
        if alias in bots:
            return security.decrypt(bots[alias])
        return None

    def _load_bots(self) -> Dict[str, str]:
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save_bots(self, data: Dict):
        with open(self.file_path, 'w') as f:
            json.dump(data, f)

bot_manager = BotManager()
