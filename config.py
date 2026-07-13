import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Provider: 'mistral', 'openai', or 'ollama'
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mistral").lower()
    
    # API Keys
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")  # <-- NEW
    
    # Ollama (local)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    
    # Other APIs
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    
    # TTS
    TTS_ENGINE = os.getenv("TTS_ENGINE", "pyttsx3")
    
    # Radio
    RADIO_STREAM = os.getenv("RADIO_STREAM", "https://zas4.ndx.co.za/proxy/bokradio?mp=/stream")
    
    # Default GPS
    DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "-26.2041"))
    DEFAULT_LON = float(os.getenv("DEFAULT_LON", "28.0473"))
