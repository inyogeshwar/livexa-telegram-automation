#!/bin/bash
# Livexa Watchdog V2
# Ensures FFmpeg runs 24/7 and restarts on failure

TARGET="$1"
INPUT_SRC="$2"
MODE="$3"

if [ -z "$TARGET" ] || [ -z "$INPUT_SRC" ]; then
    echo "Usage: ./ffmpeg_watchdog.sh <STREAM_KEY> <INPUT_SOURCE> [MODE]"
    exit 1
fi

echo "Starting Watchdog (Mode: ${MODE:-V1})..."

while true; do
    echo "[$(date)] Starting Engine..."
    # Run the engine
    bash ./ffmpeg_engine.sh "$TARGET" "$INPUT_SRC" "$MODE"
    
    EXIT_CODE=$?
    echo "FFmpeg exited with code $EXIT_CODE"
    
    echo "Restarting in 5 seconds..."
    sleep 5
done
