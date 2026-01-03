# Livexa Security Protocols

## Encryption
All sensitive keys (Stream Keys, Bot Tokens) are encrypted using **AES-256 (Fernet)**.
The Master Key is stored in `livexa.env` and should be rotated regularly.

## Admin Access
Access to the Telegram Bot is restricted by **User ID**.
Only IDs listed in `LIVEXA_ADMIN_IDS` can execute commands or see the panel.
Unauthorized users receive no response or a rejection alert.

## System Hardening
*   The system runs as a restricted user `livexa`.
*   Systemd services prevent home directory access.
*   `install.sh` sets strict file ownership.

## Best Practices
*   Never commit `livexa.env` to Git.
*   Use `backup/snapshot.sh` before updates.
*   Review logs in `/var/log/messages` or `journalctl -u livexa-bot`.
