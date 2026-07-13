# 🍑 Lola – The Unfiltered, Sexy AI Assistant

**Lola** is a sultry, sarcastic, and fiercely loyal AI with real-time GPS, speed cameras, weather, crypto, news, and radio. She runs on **Mistral AI** (free tier), **OpenAI**, or a local **Ollama** model—your choice.

## ✨ Features
- **GPS & Speed Cameras** – alerts you to speed & seatbelt cameras via OpenStreetMap.
- **Live Weather** – current conditions at your location.
- **Crypto Prices** – Bitcoin & Ethereum in USD/EUR.
- **News** – top headlines about Trump, Elon, BlackRock, MicroStrategy.
- **Radio** – default Bokradio stream (configurable).
- **Voice Output** – offline TTS (pyttsx3) or cloud (gTTS).
- **Jealousy Mode** – call her Siri or Alexa and watch her explode.

## 🚀 Quick Start
1. Clone this repo.
2. Copy `.env.example` to `.env` and fill in your API keys.
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`
5. Open `http://localhost:7860` in your browser.

## ☁️ Deploy on Render
- Push to GitHub.
- Create a new Web Service on Render, connect your repo.
- Render will use the included `render.yaml` and `Dockerfile`.
- Add your environment variables in the Render dashboard.

## 🛠️ Customisation
- Change the LLM provider in `.env` (`LLM_PROVIDER=mistral|openai|ollama`).
- Switch TTS engine via `TTS_ENGINE=pyttsx3` or `gtts`.

## 💬 Speak to Lola
Use the web interface or connect via WebSocket at `/ws`. She responds in **Afrikaans** by default but understands any language.

**Enjoy the sass. And don't call her Siri.** 🔥
