#!/bin/bash
# Livexa Cloud Backup
# Syncs playlists and config to cloud storage

SOURCE_DIR="/opt/livexa/"
REMOTE_DEST="gdrive:livexa_backups/"

echo "Starting Sync..."

# rclone sync "$SOURCE_DIR" "$REMOTE_DEST" --exclude "node_modules*"

echo "Backup complete."
