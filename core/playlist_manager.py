import os
import json
import shutil
from typing import List, Dict, Optional

STORAGE_ROOT = os.path.join(os.path.dirname(__file__), '../storage')

class PlaylistManager:
    """
    Manages playlists as directories containing media files and a metadata JSON.
    Structure: storage/<chat_id>/playlists/<playlist_name>/
    """
    def __init__(self, root_path=STORAGE_ROOT):
        self.root = root_path
        if not os.path.exists(self.root):
            os.makedirs(self.root)

    def _get_chat_root(self, chat_id: int) -> str:
        path = os.path.join(self.root, str(chat_id), 'playlists')
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def _get_playlist_path(self, chat_id: int, name: str) -> str:
        return os.path.join(self._get_chat_root(chat_id), name)

    def create_playlist(self, chat_id: int, name: str) -> bool:
        path = self._get_playlist_path(chat_id, name)
        if os.path.exists(path):
            return False
        os.makedirs(path)
        self._save_metadata(path, {"name": name, "files": []})
        self._update_concat_file(path)
        return True

    def delete_playlist(self, chat_id: int, name: str) -> bool:
        path = self._get_playlist_path(chat_id, name)
        if not os.path.exists(path):
            return False
        shutil.rmtree(path)
        return True

    def list_playlists(self, chat_id: int) -> List[str]:
        root = self._get_chat_root(chat_id)
        return [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]

    def add_file(self, chat_id: int, playlist_name: str, file_name: str, file_data: bytes) -> bool:
        path = self._get_playlist_path(chat_id, playlist_name)
        if not os.path.exists(path):
            return False
        
        # Save File
        file_path = os.path.join(path, file_name)
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Update Metadata
        meta = self._load_metadata(path)
        if file_name not in meta['files']:
            meta['files'].append(file_name)
            self._save_metadata(path, meta)
        
        self._update_concat_file(path)
        return True

    def remove_file(self, chat_id: int, playlist_name: str, file_name: str) -> bool:
        path = self._get_playlist_path(chat_id, playlist_name)
        if not os.path.exists(path):
            return False
        
        file_path = os.path.join(path, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        meta = self._load_metadata(path)
        if file_name in meta['files']:
            meta['files'].remove(file_name)
            self._save_metadata(path, meta)
            
        self._update_concat_file(path)
        return True

    def get_playlist_files(self, chat_id: int, playlist_name: str) -> List[str]:
        path = self._get_playlist_path(chat_id, playlist_name)
        if not os.path.exists(path):
            return []
        return self._load_metadata(path).get('files', [])

    def get_concat_file_path(self, chat_id: int, playlist_name: str) -> Optional[str]:
        """Returns the absolute path to the playlist.txt concat file."""
        path = self._get_playlist_path(chat_id, playlist_name)
        concat_file = os.path.join(path, 'playlist.txt')
        if os.path.exists(concat_file):
            return os.path.abspath(concat_file)
        return None

    # Helpers
    def _save_metadata(self, path: str, data: Dict):
        with open(os.path.join(path, 'playlist.json'), 'w') as f:
            json.dump(data, f)

    def _load_metadata(self, path: str) -> Dict:
        json_path = os.path.join(path, 'playlist.json')
        if not os.path.exists(json_path):
            return {"name": os.path.basename(path), "files": []}
        with open(json_path, 'r') as f:
            return json.load(f)

    def _update_concat_file(self, path: str):
        """Generates ffmpeg concat list."""
        meta = self._load_metadata(path)
        concat_path = os.path.join(path, 'playlist.txt')
        with open(concat_path, 'w') as f:
            for filename in meta.get('files', []):
                # FFmpeg concat requires absolute paths or relative safe ones
                # We use file 'filename'
                f.write(f"file '{filename}'\n")

playlist_manager = PlaylistManager()
