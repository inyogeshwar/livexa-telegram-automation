# 🌐 Professional Hosting Setup Guide (V2.3)

Follow these steps to set up your domain, Cloudflare, and Pterodactyl Panel for professional LivexaBot hosting.

---

## 1️⃣ Domain & Cloudflare Setup
1. **Cloudflare**: Add your domain to Cloudflare.
2. **DNS Records**:
   - Create an `A` record (e.g., `panel.yourdomain.com`) pointing to your VPS IP.
   - Ensure the "Proxy" status is **ON** (Orange cloud) for SSL protection.
3. **SSL/TLS**: Set encryption mode to **Full (Strict)** in Cloudflare.

---

## 2️⃣ Pterodactyl Panel Installation
If you don't have Pterodactyl installed, use the official "One-Click" script on your VPS (Ubuntu 20.04/22.04 recommended):
```bash
bash <(curl -s https://pterodactyl-installer.at)
```
*Choose option '0' to install both the Panel and Wings.*

---

## 3️⃣ Importing the Universal Egg
1. Download [livexa-universal-egg.json](./livexa-universal-egg.json) from this repository.
2. Log in to your Pterodactyl Admin Area.
3. Go to **Nests** -> Click any Nest (e.g., "Generic").
4. Click **Import Egg** and upload the JSON file.

---

## 4️⃣ deploying Your Bot
1. Go to **Servers** -> **Create New**.
2. **Nest**: Select the Nest where you imported the Egg.
3. **Egg**: Select **Livexa Universal Bot**.
4. **Environment Variables**:
   - `BOT_TOKEN`: Paste your Telegram Bot Token.
   - `ADMIN_ID`: Paste your Telegram User ID (Optional, for security).
   - `QUALITY`: Choose default quality (720p/1080p).
5. Click **Create Server**.
6. Once created, click the server, go to **Console**, and click **Start**.

---

## 🤖 Usage via Telegram
Once the bot is "Running" in your panel:
1. Message your bot `/start`.
2. Click **🔑 Set Key** and send your YouTube API Key.
3. Click **🔗 Set Source** and send a GDrive video link (or upload a file).
4. Click **🚀 Start Live** to begin streaming!

---

**Need Help?** Contact the owner: [Yogeshwar Kumar](https://github.com/inyogeshwar)
