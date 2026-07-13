import requests

class Cameras:
    @staticmethod
    def get_nearby(lat, lon, radius=2000):
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
