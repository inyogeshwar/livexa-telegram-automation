#!/usr/bin/env python3
"""
Interface to LivexaBot Stream Manager
Communicates via Unix socket
"""

import json
import socket
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self, socket_path: str = "/tmp/livexa_stream.sock"):
        self.socket_path = socket_path
    
    def _send_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect(self.socket_path)
            sock.sendall(json.dumps(command).encode() + b'\n')
            
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk: break
                response += chunk
                if b'\n' in chunk: break
            
            sock.close()
            if response: return json.loads(response.decode().strip())
        except (FileNotFoundError, ConnectionRefusedError):
            return {"status": "error", "message": "Bot not running or socket not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return None
    
    def get_status(self) -> Dict[str, Any]:
        return self._send_command({"action": "status"}) or {}
    
    def get_live_sessions(self) -> Dict[str, Any]:
        return self._send_command({"action": "list_sessions"}) or {}
    
    def start_live(self, session_id: str, media_source: str, quality: str = "auto") -> Dict[str, Any]:
        return self._send_command({"action": "start", "session_id": session_id, "media_source": media_source, "quality": quality}) or {}
    
    def stop_live(self, session_id: str) -> Dict[str, Any]:
        return self._send_command({"action": "stop", "session_id": session_id}) or {}
    
    def kill_live(self, session_id: str) -> Dict[str, Any]:
        return self._send_command({"action": "kill", "session_id": session_id}) or {}

    def restart_manager(self) -> Dict[str, Any]:
        return self._send_command({"action": "restart_manager"}) or {}
    
    def system_info(self) -> Dict[str, Any]:
        return self._send_command({"action": "system_info"}) or {}

stream_manager = StreamManager()
