import requests
from config import Config

class News:
    @staticmethod
    def get_headlines():
        if not Config.NEWS_API_KEY:
            return ["Geen nuus-sleutel nie, ek is oningelig soos 'n blok."]
        try:
            url = f"https://newsapi.org/v2/everything?q=(Trump OR Elon OR BlackRock OR MicroStrategy)&apiKey={Config.NEWS_API_KEY}&language=en&pageSize=3"
            resp = requests.get(url, timeout=5).json()
            articles = resp.get('articles', [])
            return [f"• {a['title']}" for a in articles[:3]]
        except:
            return ["Nuus API is stukkend, die wêreld is veilig vir nou."]
