# Livexa Operations Manual

## Daily Operations

### Start a Stream via Telegram
1.  Open **@LivexaBot**.
2.  Send `/start`.
3.  Click **▶ Start Live**.
4.  Select Playlist (e.g., Music).
5.  Bot will reply: "✅ Stream Dispatch signal sent!".

### Monitoring
Check system status inline:
*   Click **📊 Server Stats** in the bot menu.
*   View CPU/RAM usage and Stream Health.

### Updating Playlists
1.  Upload new MP4/MP3 files to `/opt/livexa/playlists/[category]/`.
2.  In the Telegran Bot, click **🔄 Switch Playlist** (or just Restart Stream) to refresh the file list.
3.  The system automatically re-scans the folder on every stream start.

## Troubleshooting

### Stream Dropped?
*   The **Watchdog** (`ffmpeg_watchdog.sh`) automatically restarts the stream within 5 seconds.
*   Check logs: `journalctl -u livexa-ffmpeg -f`.

### Bot Not Responding?
*   Restart the service: `systemctl restart livexa-bot`.
*   Verify your Telegram ID is in `LIVEXA_ADMIN_IDS`.

### VM Failover
*   If a VM crashes, the **Dispatcher** (v2) will route to the backup node.
*   For v1 single-node, ensure the VPS is running.
