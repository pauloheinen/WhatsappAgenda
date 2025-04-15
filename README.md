# WhatsApp Message Scheduler Bot

A Python-based WhatsApp automation tool that allows scheduling messages using Playwright and FastAPI.

## 🚀 Features

- 📱 WhatsApp Web automation
- 📅 Message scheduling 
- 🕒 Real-time status monitoring
- 🌙 Dark mode interface
- 🔄 Auto-reconnect capability
- 💾 Session persistence

## 📋 Requirements

- Python 3.12+
- Google Chrome or Chromium browser
- Windows 10/11

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/pauloheinen/WhatsappAgenda.git
cd whatsapp-scheduler-bot
```

2. Create a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

## 💻 Usage

1. Start the server:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

2. Open in your browser:
```
http://localhost:8000
```

3. Scan the WhatsApp QR code with your phone

4. Start scheduling messages!

## ⚙️ Development Setup

Required dependencies:
```pip-requirements
fastapi==0.110.0
playwright==1.42.0
uvicorn==0.27.1
python-multipart==0.0.9
jinja2==3.1.3
websockets==12.0
```

## ⚠️ Disclaimer

This project is for educational purposes only. Be aware that:

1. WhatsApp does not officially support automation
2. Your WhatsApp account may be banned if you misuse this tool
3. Use at your own risk
4. Follow WhatsApp's Terms of Service

## 🤝 Usage Guidelines

1. Don't use for spam
2. Don't send bulk messages
3. Don't harass users
4. Respect privacy and terms of service
5. Use reasonable delays between messages

## 📱 WhatsApp Web Support

The bot uses WhatsApp Web, which means:
- You need an active WhatsApp account
- Your phone must be connected to the internet
- One instance per WhatsApp account
- Session persistence between restarts

## 🔧 Configuration

The application stores data in:
- `browser_data/`: Browser session data
- `static/`: Static files
- `templates/`: HTML templates

## 🤖 Features in Detail

1. Message Scheduling:
   - Schedule messages for future delivery
   - Set date and time
   - Preview scheduled messages
   - Cancel scheduled messages

2. Connection Management:
   - Auto-reconnect on disconnection
   - Session persistence
   - Real-time status updates

3. User Interface:
   - Dark mode
   - Mobile responsive
   - Easy to use interface
   - Real-time status indicators

## 📞 Support

For support:
1. Open an issue on GitHub
2. Provide detailed error description
3. Include steps to reproduce
