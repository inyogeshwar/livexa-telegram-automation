import subprocess
import os
import signal
import time
from typing import Dict, Optional

# Constants
ENGINE_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../engine/ffmpeg_engine.sh'))

class StreamManager:
    """
    Manages active stream processes using the FFmpeg Engine script.
    Maintains state of what is running per chat_id.
    """
    def __init__(self):
        # active_streams[chat_id] = { 'process': Popen, 'key_alias': str, 'playlist': str, 'start_time': float }
        self.active_streams: Dict[int, Dict] = {}

    def start_stream(self, chat_id: int, stream_key: str, key_alias: str, playlist_concat_path: str, playlist_name: str) -> bool:
        """
        Starts a stream for a specific chat_id.
        Stops existing stream for that chat if exists.
        """
        self.stop_stream(chat_id)

        if not os.path.exists(playlist_concat_path):
             print(f"Error: Playlist file not found: {playlist_concat_path}")
             return False

        # Build command
        # We pass the Absolute Path to Playlist List File to the new engine script
        # The new engine script needs to be updated to handle a direct path if provided
        # For V2, let's assume we invoke the shell script with a special flag or just path.
        
        # We will modify ffmpeg_engine.sh to take a MODE argument or auto-detect.
        # Here we invoke a V2 wrapper or simply pass arguments.
        
        # Let's run the watchdog directly here? 
        # Actually per V2 specs: "FFmpeg lifecycle managed via stream_manager".
        # But we also need auto-heal. The watchdog script does auto-heal. 
        # So we should spawn the watchdog.
        
        watchdog_script = os.path.join(os.path.dirname(ENGINE_SCRIPT), 'ffmpeg_watchdog.sh')
        
        # The watchdog currently expects: ./ffmpeg_watchdog.sh <STREAM_KEY> <PLAYLIST_NAME>
        # But V2 uses absolute paths for playlists.
        # We must invoke the watchdog with arguments that allow it to work.
        # We will update watchdog to take: <STREAM_KEY> <PLAYLIST_PATH> <IS_V2_MODE>
        
        cmd = [
            'bash', watchdog_script,
            stream_key,
            playlist_concat_path, # Passing absolute path as 2nd arg
            "V2"                  # flag to tell script it's a V2 path
        ]
        
        try:
            # Use preexec_fn=os.setsid to allow killing the whole process group later
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                start_new_session=True 
            )
            
            self.active_streams[chat_id] = {
                'process': process,
                'key_alias': key_alias,
                'playlist': playlist_name,
                'start_time': time.time()
            }
            return True
        except Exception as e:
            print(f"Failed to start stream: {e}")
            return False

    def stop_stream(self, chat_id: int) -> bool:
        """Stops the stream for a chat_id."""
        if chat_id in self.active_streams:
            stream = self.active_streams[chat_id]
            process = stream['process']
            
            # Kill the process group (Watchdog + FFmpeg)
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except Exception:
                # Fallback if killpg fails (e.g. permission or already dead)
                try:
                    process.terminate()
                except:
                    pass
            
            del self.active_streams[chat_id]
            return True
        return False

    def get_status(self, chat_id: int) -> Optional[Dict]:
        """Returns status dict if stream is running."""
        if chat_id in self.active_streams:
            stream = self.active_streams[chat_id]
            # Check if process is still alive
            if stream['process'].poll() is None:
                return {
                    'status': 'LIVE',
                    'uptime': int(time.time() - stream['start_time']),
                    'playlist': stream['playlist'],
                    'key': stream['key_alias']
                }
            else:
                # Process died unexpectedly
                del self.active_streams[chat_id]
        return None

stream_manager = StreamManager()
