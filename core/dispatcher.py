import json
import os
import random
import requests
from typing import List, Dict

# Configuration
NODES_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/nodes.json')

class Dispatcher:
    """
    Manages stream dispatching to multiple nodes (VMs).
    Supports Round-Robin and Failover.
    """
    def __init__(self):
        self.nodes = self._load_nodes()
        self.current_index = 0

    def _load_nodes(self) -> List[Dict]:
        """Loads node list from config. Defaults to localhost if missing."""
        if not os.path.exists(NODES_CONFIG_PATH):
            return [{"name": "local-primary", "ip": "127.0.0.1", "status": "active"}]
        try:
            with open(NODES_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except:
            return [{"name": "local-primary", "ip": "127.0.0.1", "status": "active"}]

    def get_best_node(self) -> Dict:
        """
        Selects the next available node using Round-Robin.
        Checks basic health (mocked for now).
        """
        available_nodes = [n for n in self.nodes if n.get('status') == 'active']
        if not available_nodes:
            raise Exception("No active nodes available for streaming!")
        
        # Round Robin
        node = available_nodes[self.current_index % len(available_nodes)]
        self.current_index += 1
        return node

    def start_stream(self, stream_key: str, playlist: str):
        """
        Dispatches a start command to the selected node.
        """
        node = self.get_best_node()
        print(f"Dispatching stream to {node['name']} ({node['ip']})...")
        
        # In a real multi-VM setup, this would make an HTTP request to the node's agent.
        # For this standalone V1, we execute the local engine script directly if local.
        if node['ip'] in ['127.0.0.1', 'localhost']:
            cmd = f"nohup bash ../engine/ffmpeg_watchdog.sh '{stream_key}' '{playlist}' > /dev/null 2>&1 &"
            os.system(cmd)
            return True
        else:
            # Remote dispatch logic (placeholder)
            # requests.post(f"http://{node['ip']}:5000/start", json={...})
            print(f"Remote dispatch to {node['ip']} not yet implemented in V1.")
            return False

    def stop_stream(self):
        """
        Stops all streams.
        """
        # For V1, we kill local ffmpeg.
        os.system("pkill -f ffmpeg_engine.sh")
        os.system("pkill -f ffmpeg")

dispatcher = Dispatcher()
