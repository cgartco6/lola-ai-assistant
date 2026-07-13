import requests
from config import Config

class Weather:
    @staticmethod
    def get_current(lat, lon):
        if not Config.WEATHER_API_KEY:
            return "Geen weer-sleutel nie, ek weet nie of dit reën of nie."
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={Config.WEATHER_API_KEY}&units=metric&lang=af"
        try:
            resp = requests.get(url, timeout=5).json()
            temp = resp['main']['temp']
            desc = resp['weather'][0]['description']
            return f"{temp}°C, {desc} – trek 'n baadjie aan, of trek eerder uit, dis jou keuse 😉"
        except:
            return "Weer API is besig om 'n tantrum te gooi."
