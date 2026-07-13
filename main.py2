from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json, os, uuid, asyncio
from config import Config
from lola_prompt import LOLA_SYSTEM
from services.weather import Weather
from services.crypto import Crypto
from services.news import News
from services.gps import GPS
from services.cameras import Cameras
from services.radio import Radio

# ------------------------------------------------------------
# 1. LLM CLIENT SETUP (choose based on config)
# ------------------------------------------------------------
provider = Config.LLM_PROVIDER

if provider == "mistral":
    from mistralai import Mistral
    if not Config.MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY not set in .env")
    llm_client = Mistral(api_key=Config.MISTRAL_API_KEY)
    model_name = "mistral-large-latest"   # or "mistral-medium-latest"
    def call_llm(messages):
        response = llm_client.chat.complete(
            model=model_name,
            messages=messages,
            temperature=0.95,
            max_tokens=500
        )
        return response.choices[0].message.content

elif provider == "openai":
    from openai import OpenAI
    if not Config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in .env")
    llm_client = OpenAI(api_key=Config.OPENAI_API_KEY)
    model_name = "gpt-4o"   # or "gpt-3.5-turbo"
    def call_llm(messages):
        response = llm_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.95,
            max_tokens=500
        )
        return response.choices[0].message.content

elif provider == "ollama":
    from openai import OpenAI  # Ollama uses OpenAI-compatible API
    llm_client = OpenAI(
        base_url=Config.OLLAMA_BASE_URL,
        api_key="ollama"   # dummy, not used
    )
    model_name = Config.OLLAMA_MODEL
    def call_llm(messages):
        response = llm_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.95,
            max_tokens=500
        )
        return response.choices[0].message.content

else:
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Use 'mistral', 'openai', or 'ollama'.")

# ------------------------------------------------------------
# 2. TTS ENGINE SETUP
# ------------------------------------------------------------
def text_to_speech(text, filename):
    if Config.TTS_ENGINE == "pyttsx3":
        import pyttsx3
        engine = pyttsx3.init()
        engine.save_to_file(text, filename)
        engine.runAndWait()
    elif Config.TTS_ENGINE == "gtts":
        from gtts import gTTS
        tts = gTTS(text=text, lang='af', slow=False)
        tts.save(filename)
    else:
        # fallback: create empty file
        open(filename, 'a').close()

# ------------------------------------------------------------
# 3. FASTAPI APP
# ------------------------------------------------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global GPS (updated via WebSocket)
current_lat = Config.DEFAULT_LAT
current_lon = Config.DEFAULT_LON

@app.get("/")
async def get_index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def lola_chat(websocket: WebSocket):
    global current_lat, current_lon
    await websocket.accept()
    messages = [{"role": "system", "content": LOLA_SYSTEM}]
    
    try:
        while True:
            data = await websocket.receive_text()
            req = json.loads(data)
            user_msg = req.get("msg", "")
            
            # Update GPS if provided
            if req.get("lat") and req.get("lon"):
                current_lat = req["lat"]
                current_lon = req["lon"]
            
            # --- Jealousy check ---
            lower_msg = user_msg.lower()
            if any(name in lower_msg for name in ["siri", "alexa"]):
                user_msg = (f"EKSKUUS MY? Jy noem my {user_msg}? Ek is LOLA, nie daai goedkoop plastiekstem nie! "
                            f"Nou ja, hier is jou antwoord: " + user_msg)
            
            # --- Gather live data ---
            loc = GPS.get_location(current_lat, current_lon)
            weer = Weather.get_current(current_lat, current_lon)
            crypto = Crypto.get_prices()
            nuus_list = News.get_headlines()
            nuus = ', '.join(nuus_list) if nuus_list else "Geen nuus nie"
            kameras = Cameras.get_nearby(current_lat, current_lon)
            radio_url = Radio.get_stream_url()
            
            live_data = f"""
GPS: {loc}
Weer: {weer}
Crypto: {crypto}
Nuus: {nuus}
Kameras naby: {kameras['total']} (spoed: {kameras['speed_cameras']}, gordel: {kameras['seatbelt_cameras']})
Radio: {radio_url}
"""
            # Append user message with live data
            messages.append({
                "role": "user",
                "content": f"Live data: {live_data}\nVraag: {user_msg}"
            })
            
            # --- Call LLM ---
            try:
                reply = call_llm(messages)
            except Exception as e:
                reply = f"Sjoe, my brein is tans besig om 'n tantrum te gooi: {str(e)}. Probeer weer, my skat."
            
            messages.append({"role": "assistant", "content": reply})
            
            # --- TTS ---
            audio_file = f"audio/{uuid.uuid4()}.mp3"
            try:
                text_to_speech(reply, audio_file)
            except Exception as e:
                audio_file = ""  # silence is golden
            
            await websocket.send_text(json.dumps({
                "reply": reply,
                "audio": audio_file
            }))
            
    except Exception as e:
        await websocket.send_text(json.dumps({
            "reply": f"Fout: {str(e)}",
            "audio": ""
        }))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
