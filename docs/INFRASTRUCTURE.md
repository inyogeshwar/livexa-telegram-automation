# 🏗 Livexa V3 Infrastructure Guide

This document details the exact infrastructure requirements to run **Livexa V3 Enterprise Edition** reliably.

## 1. Supported Environments

Livexa V3 is designed to run on **any standard Linux Virtual Machine (VM)**. It is **NOT** locked to any specific cloud provider.

*   ✅ **Cloud VPS**: AWS EC2, Google Cloud Compute, Azure VM, DigitalOcean Droplets, Hetzner Cloud, Vultr, Linode.
*   ✅ **OpenShift Virtualization**: Runs perfectly as a KubeVirt VM.
*   ✅ **Bare Metal / On-Prem**: KVM, Proxmox, VMware ESXi.
*   ❌ **Serverless/Containers**: Not officially supported for the *engine* (Telegram bot can run anywhere, but FFmpeg requires a persistent runtime).

**Note:** No Kubernetes knowledge is required. You only need a standard Linux shell.

---

## 2. Operating System

### Primary (Recommended)
*   **OS:** **CentOS Stream 9**
*   **Why:** Enterprise stability, exact match for RHEL 9 ecosystem, robust systemd support.
*   **Testing:** Officially verified on CentOS Stream 9.

### Secondary (Compatible)
*   **OS:** Ubuntu 22.04 LTS or 24.04 LTS
*   **Support:** Fully compatible. `install.sh` detects `apt` vs `dnf` automatically.

---

## 3. Hardware Requirements

### Minimum (Home/Hobbyist)
*Suitable for 1 stream (720p/1080p 30fps) with occasional restarts.*
*   **CPU:** 2 vCPU
*   **RAM:** 2 GB - 4 GB
*   **Disk:** 20 GB SSD
*   **Network:** Stable outbound internet (residential IP ok).

### Recommended (Production / 24/7)
*Suitable for multiple streams, high-bitrate (1080p 60fps), and zero-downtime reliability.*
*   **CPU:** 4 vCPU (Dedicated preferred)
*   **RAM:** 8 GB
*   **Disk:** 50 GB+ NVMe (Space for media files)
*   **Network:** 1 Gbps Datacenter Link (AWS/Hetzner/DigitalOcean).

**Why these specs?**
FFmpeg is CPU-intensive. `libx264` encoding requires consistent CPU cycles. If CPU is stolen (shared vCPU), the stream will buffer.

---

## 4. Setup Instructions (One-Time)

You only need to do this **ONCE** when creating the server.

1.  **Create your VM/VPS.**
2.  **SSH into the server:**
    ```bash
    ssh root@<your-server-ip>
    ```
3.  **Run the automated installer:**
    ```bash
    # 1. Update OS
    dnf update -y  # (or apt update && apt upgrade -y)

    # 2. Install Git
    dnf install git -y

    # 3. Clone Livexa
    git clone https://github.com/inyogeshwar/livexa-telegram-automation.git
    cd livexa-telegram-automation

    # 4. Install
    chmod +x install.sh
    ./install.sh
    ```

4.  **Configure Secrets (One-time):**
    ```bash
    nano config/livexa.env
    # Paste your LIVEXA_BOT_TOKEN and LIVEXA_ADMIN_IDS
    ```

5.  **Start Service:**
    ```bash
    systemctl start livexa-bot
    # (Optional) Enable auto-start
    systemctl enable livexa-bot
    ```

**🛑 STOP HERE.** Close your terminal. You never need to SSH again.

---

## 5. Responsibility Matrix

| Task | 👤 User (Admin) | 🤖 Livexa Bot |
| :--- | :---: | :---: |
| **Server Provisioning** | ✅ (Day 1 only) | |
| **Install Script** | ✅ (Day 1 only) | |
| **Upload Files** | | ✅ (Telegram) |
| **Manage Playlists** | | ✅ (Telegram) |
| **Manage Stream Keys** | | ✅ (Telegram) |
| **Start/Stop Stream** | | ✅ (Telegram) |
| **Add/Remove Admins** | | ✅ (Telegram) |
| **System Updates** | | ✅ (Auto-healing) |

---

## 6. Network & Firewall

### Outbound Rules (Egress)
Allow traffic to:
*   `api.telegram.org` (HTTPS 443) - For Bot API.
*   `a.rtmp.youtube.com` (RTMP 1935) - For Streaming.
*   `pypi.org` / `rpmfusion.org` (HTTPS 443) - For installation updates.

### Inbound Rules (Ingress)
*   **SSH (22):** Open only to your IP (recommended).
*   **No other ports required.** Telegram uses Long Polling, so you do **not** need to open port 443 or configure webhooks.

---

## 7. Troubleshooting

*   **Logs:** `journalctl -u livexa-bot -f`
*   **Status:** `systemctl status livexa-bot`
*   **Restart:** `systemctl restart livexa-bot`
