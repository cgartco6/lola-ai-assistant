import requests
from geopy.geocoders import Nominatim

class GPS:
    @staticmethod
    def get_location(lat, lon):
        try:
            geolocator = Nominatim(user_agent="lola_ai")
            loc = geolocator.reverse(f"{lat}, {lon}")
            return loc.address if loc else "Ergens in die bos, my skat"
        except:
            return "GPS is tans dronk, probeer later."
