from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import json, os, uuid, asyncio, math
from config import Config
from lola_prompt import LOLA_SYSTEM
from services.weather import Weather
from services.crypto import Crypto
from services.news import News
from services.gps import GPS
from services.cameras import Cameras
from services.radio import Radio
from services.traffic import Traffic
from services.supabase import Memory
import folium

# ------------------------------------------------------------
# 1. LLM CLIENT SETUP
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
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

# ------------------------------------------------------------
# 2. TTS ENGINE
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
# 3. FASTAPI APP + Memory
# ------------------------------------------------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

memory = Memory()

# Global GPS & speed
current_lat = Config.DEFAULT_LAT
current_lon = Config.DEFAULT_LON
current_speed = 0  # km/h, will be updated from client

# Map generation endpoint
@app.get("/map")
async def get_map():
    m = folium.Map(location=[current_lat, current_lon], zoom_start=14)
    folium.Marker([current_lat, current_lon], popup="You are here").add_to(m)
    # Add cameras
    cameras = Cameras.get_nearby(current_lat, current_lon)
    # For each camera, we would need coordinates – but we don't store them here
    # For simplicity, we add a circle for each camera type
    folium.Circle(
        location=[current_lat, current_lon],
        radius=100,
        color="red",
        fill=True,
        popup=f"Speed cameras nearby: {cameras['speed_cameras']}"
    ).add_to(m)
    map_path = "static/map.html"
    m.save(map_path)
    return HTMLResponse(open(map_path).read())

@app.get("/")
async def get_index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def lola_chat(websocket: WebSocket):
    global current_lat, current_lon, current_speed
    await websocket.accept()
    messages = [{"role": "system", "content": LOLA_SYSTEM}]
    user_id = str(uuid.uuid4())  # generate a unique user ID for this session (could be improved)
    
    # Load recent memory (last 5 exchanges)
    if memory.enabled:
        history = memory.get_recent_messages(user_id, limit=5)
        for entry in history:
            messages.append({"role": entry['role'], "content": entry['content']})
    
    try:
        while True:
            data = await websocket.receive_text()
            req = json.loads(data)
            user_msg = req.get("msg", "")
            # Update GPS & speed if provided
            if req.get("lat") and req.get("lon"):
                current_lat = req["lat"]
                current_lon = req["lon"]
            if req.get("speed") is not None:
                current_speed = req["speed"]
            
            # --- Jealousy check ---
            ai_names = ["siri", "alexa", "google assistant", "cortana", "bixby", "gemini", "grok", "claude", "copilot", "deepseek", "perplexity", "chatgpt", "bard"]
            lower_msg = user_msg.lower()
            if any(name in lower_msg for name in ai_names):
                user_msg = (f"EKSKUUS MY? Jy noem my {user_msg}? Ek is LOLA, nie daai goedkoop plastiekstem nie! "
                            f"Nou ja, hier is jou antwoord: " + user_msg)
            
            # --- Road rage detection ---
            anger_words = ["fuck", "idiot", "stupid", "angry", "rage", "pissed", "dumbass", "kak", "moer"]
            if any(word in lower_msg for word in anger_words):
                user_msg = f"[USER IS ANGRY – please calm them down with a soothing, sassy tone] {user_msg}"
            
            # --- Gather live data ---
            loc = GPS.get_location(current_lat, current_lon)
            weer = Weather.get_current(current_lat, current_lon)
            crypto = Crypto.get_prices()
            nuus_list = News.get_headlines()
            nuus = ', '.join(nuus_list) if nuus_list else "Geen nuus nie"
            kameras = Cameras.get_nearby(current_lat, current_lon)
            
            # --- Speed limit & proactive alert ---
            speed_limit = Cameras.get_speed_limit(current_lat, current_lon)
            speed_alert = ""
            if speed_limit and current_speed > 0:
                if current_speed > speed_limit + Config.SPEED_ALERT_THRESHOLD:
                    speed_alert = f"⚠️ JY JAAG! Spoed: {current_speed} km/h, limiet: {speed_limit} km/h. Trek jou voet uit, my skat."
                elif current_speed > speed_limit:
                    speed_alert = f"⚠️ Pasop, jy is {current_speed - speed_limit} km/h bo die limiet. Die fopse kan enige plek wees."
                else:
                    speed_alert = f"✅ Spoed is binne perke ({current_speed}/{speed_limit} km/h). Goed so, my liefie."
            else:
                speed_alert = "Geen spoedlimiet data nie – ry maar volgens jou gewete (of hou jou oë oop)."
            
            # Traffic & roadblocks
            traffic_alerts = Traffic.get_incidents(current_lat, current_lon)
            traffic_text = " | ".join(traffic_alerts) if traffic_alerts else "Geen verkeerswaarskuwings nie."
            osm_blocks = Cameras.get_roadblocks(current_lat, current_lon)
            osm_text = " | ".join(osm_blocks) if osm_blocks else "Geen OSM-versperrings nie."
            radio_url = Radio.get_stream_url()
            
            live_data = f"""
GPS: {loc}
Weer: {weer}
Crypto: {crypto}
Nuus: {nuus}
Kameras naby: {kameras['total']} (spoed: {kameras['speed_cameras']}, gordel: {kameras['seatbelt_cameras']})
Spoed: {current_speed} km/h | Limiet: {speed_limit if speed_limit else 'Onbekend'}
🚦 Spoedwaarskuwing: {speed_alert}
🚨 Polisie & blokkades: {traffic_text}
🚧 Statiese versperrings: {osm_text}
Radio: {radio_url}
"""
            # Append user message with live data
            messages.append({
                "role": "user",
                "content": f"Live data: {live_data}\nVraag: {user_msg}"
            })
            
            # Store user message in memory
            if memory.enabled:
                memory.store_message(user_id, "user", user_msg, {"lat": current_lat, "lon": current_lon, "speed": current_speed})
            
            # --- Call LLM ---
            try:
                reply = call_llm(messages)
            except Exception as e:
                reply = f"Sjoe, my brein is tans besig om 'n tantrum te gooi: {str(e)}. Probeer weer, my skat."
            
            messages.append({"role": "assistant", "content": reply})
            
            # Store assistant message
            if memory.enabled:
                memory.store_message(user_id, "assistant", reply, {})
            
            # --- TTS ---
            audio_file = f"audio/{uuid.uuid4()}.mp3"
            try:
                text_to_speech(reply, audio_file)
            except Exception as e:
                audio_file = ""
            
            # --- Send response ---
            await websocket.send_text(json.dumps({
                "reply": reply,
                "audio": audio_file,
                "speed_alert": speed_alert  # optionally display on frontend
            }))
            
    except Exception as e:
        await websocket.send_text(json.dumps({
            "reply": f"Fout: {str(e)}",
            "audio": ""
        }))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
