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
from services.traffic import Traffic  # <-- NEW

# ------------------------------------------------------------
# 1. LLM CLIENT SETUP (choose based on config)
# ------------------------------------------------------------
provider = Config.LLM_PROVIDER

if provider == "mistral":
    from mistralai import Mistral
    if not Config.MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY not set in .env")
    llm_client = Mistral(api_key=Config.MISTRAL_API_KEY)
    model_name = "mistral-large-latest"
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
    model_name = "gpt-4o"
    def call_llm(messages):
        response = llm_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.95,
            max_tokens=500
        )
        return response.choices[0].message.content

elif provider == "ollama":
    from openai import OpenAI
    llm_client = OpenAI(
        base_url=Config.OLLAMA_BASE_URL,
        api_key="ollama"
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
        open(filename, 'a').close()

# ------------------------------------------------------------
# 3. FASTAPI APP
# ------------------------------------------------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

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
            
            # --- NEW: Traffic incidents (Police, Roadblocks, Accidents) ---
            traffic_alerts = Traffic.get_incidents(current_lat, current_lon)
            traffic_text = " | ".join(traffic_alerts) if traffic_alerts else "Geen verkeerswaarskuwings nie."
            
            # --- NEW: Static roadblocks from OSM ---
            osm_blocks = Cameras.get_roadblocks(current_lat, current_lon)
            osm_text = " | ".join(osm_blocks) if osm_blocks else "Geen OSM-versperrings nie."
            
            radio_url = Radio.get_stream_url()
            
            live_data = f"""
GPS: {loc}
Weer: {weer}
Crypto: {crypto}
Nuus: {nuus}
Kameras naby: {kameras['total']} (spoed: {kameras['speed_cameras']}, gordel: {kameras['seatbelt_cameras']})
🚨 POLISIE & PADBLOKKADES (TomTom): {traffic_text}
🚧 STATIESE VERSperrings (OSM): {osm_text}
Radio: {radio_url}
"""
            messages.append({
                "role": "user",
                "content": f"Live data: {live_data}\nVraag: {user_msg}"
            })
            
            try:
                reply = call_llm(messages)
            except Exception as e:
                reply = f"Sjoe, my brein is tans besig om 'n tantrum te gooi: {str(e)}. Probeer weer, my skat."
            
            messages.append({"role": "assistant", "content": reply})
            
            audio_file = f"audio/{uuid.uuid4()}.mp3"
            try:
                text_to_speech(reply, audio_file)
            except Exception as e:
                audio_file = ""
            
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
