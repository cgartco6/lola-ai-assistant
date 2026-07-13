import requests
from config import Config

class Traffic:
    @staticmethod
    def get_incidents(lat, lon, radius=3000):
        """Fetch live traffic incidents (police, road closures, accidents) from TomTom."""
        if not Config.TOMTOM_API_KEY:
            return ["🔴 Geen TomTom-sleutel nie – ek kan nie die fopse sien nie, ry maar vinnig."]
        
        url = f"https://api.tomtom.com/traffic/services/5/incidentDetails"
        params = {
            "key": Config.TOMTOM_API_KEY,
            "point": f"{lat},{lon}",
            "radius": radius,
            "language": "en-US",
            "projection": "EPSG:4326",
            "includeLocationCodes": "false",
            "version": "true"
        }
        
        try:
            resp = requests.get(url, params=params, timeout=8).json()
            incidents = resp.get("incidents", [])
            alerts = []
            
            for inc in incidents[:5]:  # Max 5 nearest
                props = inc.get("properties", {})
                events = props.get("events", [])
                if not events:
                    continue
                event_type = events[0].get("code", "UNKNOWN")
                # Map TomTom codes to sexy warnings
                if "ROAD_CLOSED" in event_type:
                    alerts.append(f"🚧 PADBLOKKADE – {props.get('description', 'Tydelike pad toe')}")
                elif "POLICE" in event_type:
                    alerts.append(f"👮‍♀️ POLISIE voor – {props.get('description', 'Kontrolepunt of ongeluk')}")
                elif "ACCIDENT" in event_type:
                    alerts.append(f"💥 ONGELUK melding – {props.get('description', 'Ry versigtig, my skat')}")
                elif "HAZARD" in event_type or "OBSTRUCTION" in event_type:
                    alerts.append(f"⚠️ GEVAAR – {props.get('description', 'Obstruksie op die pad')}")
                elif "CONSTRUCTION" in event_type:
                    alerts.append(f"🚧 KONSTRUKSIE – {props.get('description', 'Ry maar stadig, of draai om')}")
            
            if not alerts:
                return ["✅ Geen polisie of padblokkades naby nie – ry soos `n dronk aap as jy wil."]
            return alerts
            
        except Exception as e:
            return [f"🔴 My TomTom-verbinding is besig om te kak: {str(e)}. Ry maar blind."]
