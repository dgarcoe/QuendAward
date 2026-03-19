# 🎙️ QuendAward

**Special Callsign Operator Coordination Tool for Ham Radio**

A web application for coordinating multiple operators activating the same special callsign. Avoid conflicts by blocking band/mode combinations in real-time.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-GPLv3-blue.svg)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 **Real-time Heatmap** | Interactive visualization of band/mode availability |
| 🔒 **Band/Mode Blocking** | Reserve combinations while you're active |
| 💬 **Real-time Chat** | MQTT-powered instant messaging between operators (no page refresh) |
| 📡 **DX Cluster Spotting** | Send spots to DX Cluster nodes via Telnet to announce activity |
| 📢 **Announcements** | Admin announcements with notification badges |
| 🏆 **Multi-Award Support** | Manage multiple special callsigns/events |
| 🌍 **Multi-Language** | English, Spanish, Galician |
| 📱 **Mobile-Friendly** | Responsive design for smartphones |
| 👥 **Multi-Operator** | Secure authentication for teams |
| 💾 **Backup/Restore** | Database management for admins |
| 🤖 **Telegram Bot** | Block/unblock bands and receive notifications via Telegram |

---

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Clone and configure
git clone <repository-url>
cd award_planner
cp .env.example .env
# Edit .env with your admin credentials

# Run
docker-compose up -d

# Access at http://localhost:8501
```

### Manual Installation

```bash
pip install -r requirements.txt
export ADMIN_CALLSIGN=EA1RFI
export ADMIN_PASSWORD=YourSecurePassword
streamlit run app.py
```

---

## ⚙️ Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `ADMIN_CALLSIGN` | Super admin callsign | Yes |
| `ADMIN_PASSWORD` | Super admin password | Yes |
| `DATABASE_PATH` | SQLite database path | No (default: `ham_coordinator.db`) |
| `MQTT_WS_URL` | MQTT WebSocket URL for real-time chat (e.g. `wss://yourdomain.com/mqtt`) | No (chat disabled when unset) |
| `MQTT_BROKER_HOST` | MQTT broker hostname (internal) | No (default: `mosquitto`) |
| `MQTT_BROKER_PORT` | MQTT broker port (internal) | No (default: `1883`) |
| `DX_CLUSTER_HOST` | DX Cluster node hostname (e.g. `dxfun.com`) | No (spotting disabled when unset) |
| `DX_CLUSTER_PORT` | DX Cluster Telnet port | No (default: `7300`) |
| `DX_CLUSTER_CALLSIGN` | Callsign used to log in to the cluster | No |
| `DX_CLUSTER_PASSWORD` | Password for cluster authentication (if required) | No |
| `TELEGRAM_BOT_TOKEN` | Telegram bot API token from @BotFather | No (bot disabled when unset) |

---

## 💬 Real-time Chat

QuendAward includes a real-time chat system powered by MQTT over WebSockets. Messages are delivered instantly between operators — no page refresh needed.

### How it works

```
Browser A ──(MQTT/WS)──► Mosquitto Broker ──(MQTT/WS)──► Browser B
                                │
                         Python subscriber ──► SQLite (history)
```

- **Mosquitto** MQTT broker runs as a Docker sidecar, handling pub/sub routing
- **mqtt.js** in the browser connects via WebSocket for instant message delivery
- A **Python MQTT subscriber** thread persists messages to SQLite for chat history
- Chat rooms are **per-award** — each special callsign has its own channel

### Enabling chat

Set the `MQTT_WS_URL` environment variable to enable the chat tab:

```bash
# In .env
MQTT_WS_URL=wss://yourdomain.com/mqtt
```

When `MQTT_WS_URL` is not set, the chat tab is hidden and no MQTT connections are made. The nginx config included in the standalone deployment already proxies `/mqtt` to Mosquitto's WebSocket port.

---

## 📡 DX Cluster Spotting

Operators can send spots to a DX Cluster node directly from the activity dashboard, announcing that a special callsign is active on a specific frequency.

### How it works

1. An operator **blocks a band/mode** on the heatmap (spotting requires an active block)
2. The **DX Cluster Spot** section appears below the heatmap with band/mode autofilled from the block
3. The operator enters the **spotted callsign**, **frequency**, and an optional **comment**
4. QuendAward connects to the configured DX Cluster node via Telnet and sends the spot command

```
DX de EA1RFI:    14025.0  EG90IARU     QRV CW                        1423Z
     └─ cluster login      └─ spotted    └─ comment
```

### Configuration

Set the following environment variables to enable spotting:

```bash
# In .env
DX_CLUSTER_HOST=dxfun.com
DX_CLUSTER_PORT=8000
DX_CLUSTER_CALLSIGN=EA1RFI
DX_CLUSTER_PASSWORD=           # Only if the cluster requires authentication
```

When `DX_CLUSTER_HOST` is not set, the send button shows a configuration error. The spot section is always visible but requires an active block to use. Clusters that require password authentication after the callsign login are supported via the optional `DX_CLUSTER_PASSWORD` variable.

---

## 🤖 Telegram Bot

QuendAward includes an optional Telegram bot that allows operators to manage band/mode blocks and receive real-time notifications directly from Telegram.

### Features

- **Link operator accounts** to Telegram via `/link` command
- **Block/unblock bands** interactively with inline keyboards
- **View current blocks** for your selected award
- **Real-time notifications** when other operators block, unblock, or switch bands
- **Chat mention alerts** when someone @mentions you in the web chat
- **Multi-language support** (English, Spanish, Galician)
- **Per-user settings** for default award, notifications, and language

### Setup

1. **Create a Telegram bot**:
   - Open Telegram and message [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow the prompts
   - Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Configure the bot token**:
   ```bash
   # In .env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

3. **Run the bot** (via Docker Compose or manually):
   ```bash
   # Included automatically in docker-compose up
   # OR manually:
   python services/telegram_bot.py
   ```

### Using the bot

1. **Link your account**: Open your bot on Telegram and send:
   ```
   /link <your_callsign> <your_password>
   ```

2. **Set your default award**:
   ```
   /awards              # List available awards
   /setaward <id>       # Set your default award
   ```

3. **Manage blocks**:
   ```
   /block               # Interactive block selection
   /myblocks            # View your blocks
   /unblock             # Release all your blocks
   /blocks              # View all blocks for current award
   ```

4. **Configure preferences**:
   ```
   /notifications on    # Enable notifications
   /lang en             # Set language (en/es/gl)
   /status              # View your settings
   ```

### How notifications work

When linked operators have notifications enabled:
- Get notified when **other operators** block, unblock, or switch bands in your default award
- Receive alerts when someone **@mentions** your callsign in the web chat
- Notifications respect your language preference

Set your default award with `/setaward <id>` to receive relevant block notifications for that special callsign.

---

## 📁 Project Structure

```
award_planner/
├── app.py               # Main application entry point
├── config.py            # Configuration constants
├── database.py          # Database compatibility layer
├── Dockerfile
│
├── core/                # Core modules
│   ├── database.py      # SQLite connection & schema
│   └── auth.py          # Authentication & password hashing
│
├── features/            # Feature modules
│   ├── announcements.py # Admin announcements
│   ├── awards.py        # Special callsign management
│   ├── blocks.py        # Band/mode blocking logic
│   ├── chat.py          # Chat message persistence
│   ├── dx_cluster.py    # DX Cluster Telnet spotting
│   └── backup.py        # Database backup/restore
│
├── services/            # Background services
│   └── mqtt_subscriber.py  # MQTT listener for chat persistence
│
├── ui/                  # User interface components
│   ├── admin_panel.py   # Admin panel tabs
│   ├── components.py    # Reusable UI components
│   ├── charts.py        # Plotly visualizations
│   ├── chat_widget.py   # Real-time chat (HTML/JS/CSS)
│   └── styles.py        # Responsive CSS/JS
│
├── i18n/                # Internationalization
│   └── translations.py  # Translations (EN/ES/GL)
│
├── mosquitto/           # MQTT broker config
│   └── config/
│       └── mosquitto.conf
│
├── nginx/               # Reverse proxy config
│   └── nginx.conf
│
├── docker-compose.yml
└── docker-compose-standalone.yml
```

---

## 📻 Supported Bands & Modes

**Bands:** 160m, 80m, 60m, 40m, 30m, 20m, 17m, 15m, 12m, 10m, 8m, 6m, 2m, 70cm, SAT

**Modes:** SSB, CW, FT8, FT4, RTTY

---

## 🔐 User Roles

| Role | Capabilities |
|------|-------------|
| **Super Admin** | Full access, configured via environment variables |
| **Admin** | Create operators, manage awards, announcements |
| **Operator** | Block/unblock bands, view dashboard, chat |

---

## 📖 Usage

### For Admins

1. Login with admin credentials
2. **Create Operators**: Admin Panel → Create Operator
3. **Create Awards**: Admin Panel → Special Callsigns
4. **Post Announcements**: Admin Panel → Announcements

### For Operators

1. Login with provided credentials
2. Select the active award/special callsign
3. Click on heatmap cells to block/unblock
4. Check 🔔 for announcements
5. Use the 💬 Chat tab to communicate with other operators in real time

---

## 🌍 Languages

- 🇬🇧 English
- 🇪🇸 Español
- 🇬🇱 Galego (default)

Select language on the login page.

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** (GPLv3).

See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Daniel García Coego (EA1RFI)**

---

## 🤝 Contributing

Contributions welcome! Please open an issue or pull request.
