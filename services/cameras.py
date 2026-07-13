import requests

class Cameras:
    @staticmethod
    def get_nearby(lat, lon, radius=2000):
        # unchanged...
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        (
          node["highway"="speed_camera"](around:{radius},{lat},{lon});
          node["enforcement"="seatbelt"](around:{radius},{lat},{lon});
        );
        out body;
        """
        try:
            resp = requests.get(overpass_url, params={"data": query}, timeout=10)
            data = resp.json()
            speed = [n for n in data['elements'] if n.get('tags',{}).get('highway') == 'speed_camera']
            seatbelt = [n for n in data['elements'] if n.get('tags',{}).get('enforcement') == 'seatbelt']
            return {
                "speed_cameras": len(speed),
                "seatbelt_cameras": len(seatbelt),
                "total": len(speed) + len(seatbelt)
            }
        except:
            return {"speed_cameras": 0, "seatbelt_cameras": 0, "total": 0}

    @staticmethod
    def get_roadblocks(lat, lon, radius=2000):
        # unchanged...
        pass  # existing code

    # NEW: Get speed limit for current road using TomTom or OSM
    @staticmethod
    def get_speed_limit(lat, lon):
        # TomTom Speed Limits API (free tier)
        # Alternatively, fallback to OSM "maxspeed" tag
        # We'll try TomTom first, then OSM
        from config import Config
        if Config.TOMTOM_API_KEY:
            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
            params = {
                "key": Config.TOMTOM_API_KEY,
                "point": f"{lat},{lon}",
                "speedUnit": "KPH"
            }
            try:
                resp = requests.get(url, params=params, timeout=5).json()
                speed = resp.get('flowSegmentData', {}).get('currentSpeed')
                if speed:
                    return int(speed)
            except:
                pass
        # Fallback: OSM reverse geocode to get maxspeed tag
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        way(around:50,{lat},{lon})["highway"]["maxspeed"];
        out tags;
        """
        try:
            resp = requests.get(overpass_url, params={"data": query}, timeout=10)
            data = resp.json()
            for element in data.get('elements', []):
                maxspeed = element.get('tags', {}).get('maxspeed')
                if maxspeed:
                    # if it's like "80" or "80 km/h" parse
                    speed = ''.join(filter(str.isdigit, maxspeed))
                    if speed:
                        return int(speed)
        except:
            pass
        return None  # unknown
