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

    # NEW: Static roadblocks & barriers from OSM
    @staticmethod
    def get_roadblocks(lat, lon, radius=2000):
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        (
          node["barrier"](around:{radius},{lat},{lon});
          node["highway"="roadblock"](around:{radius},{lat},{lon});
          node["highway"="construction"](around:{radius},{lat},{lon});
          node["obstacle"](around:{radius},{lat},{lon});
        );
        out body;
        """
        try:
            resp = requests.get(overpass_url, params={"data": query}, timeout=10)
            data = resp.json()
            barriers = []
            for n in data['elements']:
                tags = n.get('tags', {})
                barrier_type = tags.get('barrier', '')
                if barrier_type in ['gate', 'lift_gate', 'block', 'bollard', 'sally_port']:
                    barriers.append(f"🚧 Hek/versperring ({barrier_type})")
                elif tags.get('highway') == 'roadblock':
                    barriers.append("🚧 Padblokkade (OSM)")
                elif tags.get('highway') == 'construction':
                    barriers.append("🚧 Konstruksie-area")
                elif tags.get('obstacle'):
                    barriers.append(f"⚠️ Obstakel: {tags.get('obstacle')}")
            return barriers[:5] if barriers else ["Geen OSM-versperrings naby nie."]
        except:
            return ["Kon nie OSM-versperrings laai nie."]
