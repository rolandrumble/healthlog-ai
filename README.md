<p align="center">
  <img src="assets/logo.svg" alt="HealthLog AI Logo" width="120" height="120">
</p>

<h1 align="center">🏥 HealthLog AI - Personal Health Companion</h1>

<p align="center">
  <strong>AI-powered health tracking with meal photo analysis, symptom logging, and personalized insights</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#demo">Demo</a> •
  <a href="#installation">Installation</a> •
  <a href="#telegram-bot">Telegram Bot</a> •
  <a href="#api">API</a> •
  <a href="#deployment">Deployment</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/LLaMA_3-Vision_AI-FF6F00?style=for-the-badge&logo=meta&logoColor=white" alt="LLaMA 3">
  <img src="https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram">
</p>

---

## ⚠️ Medical Disclaimer

> **This application is for EDUCATIONAL and INFORMATIONAL purposes only.** It does NOT provide medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for medical concerns.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 📸 AI Meal Analysis
Snap a photo of your food and get instant nutritional estimates powered by LLaMA 3 Vision AI.

### 📝 Symptom Tracking
Log symptoms with severity ratings. AI identifies patterns and correlations over time.

### 💊 Medication Manager
Track medications, log doses, and monitor your adherence rate.

</td>
<td width="50%">

### 📊 Health Insights
Get personalized AI-powered insights based on your health data patterns.

### 🤖 Telegram Bot
Track everything via Telegram - send photos, log symptoms, get reports on the go.

### 📄 Weekly Reports
Generate comprehensive health reports to share with your healthcare provider.

</td>
</tr>
</table>

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI (Python 3.9+) |
| **AI/Vision** | Groq API (LLaMA 3.2 90B Vision) |
| **Database** | SQLite |
| **Bot** | python-telegram-bot |
| **Frontend** | HTML5, CSS3, JavaScript |

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- [Groq API Key](https://console.groq.com/) (FREE)
- [Telegram Bot Token](https://t.me/BotFather) (for bot features)

### Quick Start

```bash
# Clone repository
git clone https://github.com/rolandrumble/healthlog-ai.git
cd healthlog-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
python main.py
```

Open http://localhost:8000 in your browser.

---

## 🤖 Telegram Bot Setup

### Step 1: Create Bot with BotFather
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow prompts
3. Copy your bot token

### Step 2: Configure
Add to your `.env`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
API_BASE_URL=http://localhost:8000
```

### Step 3: Run Bot
```bash
python bot/telegram_bot.py
```

### Bot Commands
| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/symptom` | Log a symptom |
| `/meds` | Manage medications |
| `/report` | Get weekly report |
| `/insights` | AI health insights |
| 📸 Send photo | Log meal with AI analysis |

---

## 📡 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Home page |
| `GET` | `/dashboard` | User dashboard |
| `POST` | `/api/auth/signup` | Register user |
| `POST` | `/api/auth/login` | Login |
| `POST` | `/api/meals/log` | Log meal (with photo) |
| `GET` | `/api/meals/{user_id}` | Get meals |
| `POST` | `/api/symptoms/log` | Log symptom |
| `GET` | `/api/symptoms/{user_id}/analysis` | AI symptom analysis |
| `POST` | `/api/medications/add` | Add medication |
| `GET` | `/api/medications/{user_id}/adherence` | Adherence stats |
| `POST` | `/api/daily-score` | Log daily check-in |
| `GET` | `/api/insights/{user_id}` | Health insights |
| `GET` | `/api/report/{user_id}` | Weekly report |
| `POST` | `/api/chat` | AI health chat |

### Example: Log Meal with Photo

```bash
curl -X POST "http://localhost:8000/api/meals/log" \
  -F "file=@meal.jpg" \
  -F "meal_type=lunch" \
  -F "user_id=user123"
```

---

## 🌐 Deployment

### Railway (Recommended)
1. Push to GitHub
2. Go to [railway.app](https://railway.app)
3. New Project → Deploy from GitHub
4. Add environment variables
5. Done! 🎉

### Render
```bash
# Build: pip install -r requirements.txt
# Start: uvicorn server.main:app --host 0.0.0.0 --port $PORT
```

### Docker
```bash
docker build -t healthlog-ai .
docker run -d -p 8000:8000 -e GROQ_API_KEY=your_key healthlog-ai
```

---

## 📂 Project Structure

```
healthlog-ai/
├── server/
│   ├── __init__.py
│   └── main.py           # FastAPI application
├── bot/
│   ├── __init__.py
│   └── telegram_bot.py   # Telegram bot
├── static/
│   ├── css/
│   └── js/
├── templates/
│   ├── index.html
│   └── dashboard.html
├── database/             # SQLite database
├── uploads/              # Meal photos
├── reports/              # Generated reports
├── requirements.txt
├── Dockerfile
├── vercel.json
├── railway.json
└── README.md
```

---

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for AI | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | For bot |
| `API_BASE_URL` | Backend URL for bot | For bot |

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file.

---

<p align="center">
  <strong>⭐ Star this repo if you find it helpful!</strong>
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/rolandrumble">Roland</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Remember-Not_Medical_Advice-red?style=for-the-badge" alt="Disclaimer">
</p>
