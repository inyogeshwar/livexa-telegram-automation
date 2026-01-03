import os
import json
from typing import Dict, Any

STORAGE_ROOT = os.path.join(os.path.dirname(__file__), '../storage')

class StateManager:
    """
    Persists UI state per chat to support auto-resume after bot restart.
    Storage: storage/<chat_id>/state.json
    """
    def __init__(self, root_path=STORAGE_ROOT):
        self.root = root_path
        if not os.path.exists(self.root):
            os.makedirs(self.root)

    def _get_state_file(self, chat_id: int) -> str:
        path = os.path.join(self.root, str(chat_id))
        if not os.path.exists(path):
            os.makedirs(path)
        return os.path.join(path, 'state.json')

    def save_state(self, chat_id: int, state: Dict[str, Any]):
        path = self._get_state_file(chat_id)
        # Merge with existing
        current = self.get_state(chat_id)
        current.update(state)
        
        with open(path, 'w') as f:
            json.dump(current, f)

    def get_state(self, chat_id: int) -> Dict[str, Any]:
        path = self._get_state_file(chat_id)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def clear_state(self, chat_id: int):
        path = self._get_state_file(chat_id)
        if os.path.exists(path):
            os.remove(path)

state_manager = StateManager()
