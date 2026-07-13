import requests

class Crypto:
    @staticmethod
    def get_prices():
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd,eur"
            data = requests.get(url, timeout=5).json()
            btc = data['bitcoin']['usd']
            eth = data['ethereum']['usd']
            return f"BTC: ${btc} | ETH: ${eth} – Koop of huil, dis jou geld."
        except:
            return "Crypto-markte is mal, ek kry geen prys nie."
