import os
import json
from typing import Set, List

STORAGE_ROOT = os.path.join(os.path.dirname(__file__), '../storage')

class AdminManager:
    """
    Manages the list of authorized admin IDs dynamically.
    Storage: storage/admins.json
    """
    def __init__(self, root_path=STORAGE_ROOT):
        self.root = root_path
        self.file_path = os.path.join(self.root, 'admins.json')
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        
        # Initialize from ENV if empty
        if not os.path.exists(self.file_path):
            initial_admins = self._load_from_env()
            self._save_admins(initial_admins)

    def _load_from_env(self) -> List[int]:
        raw = os.getenv('LIVEXA_ADMIN_IDS', '')
        return [int(x.strip()) for x in raw.split(',') if x.strip().isdigit()]

    def get_admins(self) -> Set[int]:
        if not os.path.exists(self.file_path):
            return set()
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                return set(data.get('admins', []))
        except:
            return set()

    def add_admin(self, user_id: int):
        admins = self.get_admins()
        admins.add(user_id)
        self._save_admins(list(admins))

    def remove_admin(self, user_id: int):
        admins = self.get_admins()
        if user_id in admins:
            admins.remove(user_id)
            self._save_admins(list(admins))

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.get_admins()

    def _save_admins(self, admins: List[int]):
        with open(self.file_path, 'w') as f:
            json.dump({"admins": list(admins)}, f)

admin_manager = AdminManager()
