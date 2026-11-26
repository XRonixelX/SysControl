# ⚡ SysControl — Full System Manager for Windows

Modern, dark-themed Windows system management tool with real-time monitoring and Telegram integration.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

### 📊 Dashboard
- Real-time CPU, RAM, GPU usage with animated progress bars
- Per-core CPU monitoring
- Live network speed (upload / download)
- Disk usage overview

### 💻 Hardware Info
- Full system specs: OS, CPU, RAM, GPU, temperatures
- MAC address, hostname, uptime, boot time

### 📋 Process Manager
- View top processes sorted by CPU/RAM usage
- Kill processes with one click
- Color-coded high-usage indicators

### 🌐 Network Monitor
- All network interfaces with IP addresses
- Total traffic (sent/received)
- Live upload/download speed
- Active connections list

### 💾 Disk Manager
- All partitions with usage bars
- Read/Write I/O statistics
- Color-coded warnings for full disks

### 🔧 Services Manager
- List all Windows services
- Status indicators (running/stopped)
- Search and filter

### 🚀 Startup Programs
- View all auto-start programs
- User vs System scope

### 📱 Telegram Integration
- Send full system reports to Telegram
- Configure bot token and chat ID
- Test connection
- Step-by-step setup guide included

### ⚙️ Power & System Control
- Restart Explorer
- Clear Temp Files
- Flush DNS
- Lock Screen / Sleep / Restart / Shutdown
- Confirmation dialogs for dangerous actions

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/XRonixelX/SysControl.git
cd SysControl

# Run (auto-installs dependencies)
run.bat

# Or manually:
pip install -r requirements.txt
python main.py
```

## 📱 Telegram Setup
1. Open Telegram → search **@BotFather** → `/newbot` → copy the **token**
2. Send a message to your new bot
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Find your **chat_id** in the response
5. Enter both in the Telegram tab of SysControl

## 🛠 Requirements
- Python 3.9+
- Windows 10/11

## 📄 License
MIT License — By Ronixel
