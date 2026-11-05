import requests
import time
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "AirspaceTracker/1.0"


def get_country_bbox(country_name: str):
    """Возвращает (lat, lon, boundingbox) для страны."""
    params = {"q": country_name, "format": "json", "limit": 1, "polygon_geojson": 0}
    resp = requests.get(
        NOMINATIM_URL, params=params, headers={"User-Agent": USER_AGENT}
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return None
    item = data[0]
    lat = float(item["lat"])
    lon = float(item["lon"])
    bbox = [float(x) for x in item["boundingbox"]]
    time.sleep(1.1)
    return lat, lon, bbox


OPENSKY_URL = "https://opensky-network.org/api/states/all"


def get_airplanes_in_bbox(bbox):
    """
    Возвращает список state vectors.
    """
    params = {"lamin": bbox[0], "lamax": bbox[1], "lomin": bbox[2], "lomax": bbox[3]}
    resp = requests.get(OPENSKY_URL, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"OpenSky error: {resp.status_code}")
        return []
    data = resp.json()
    return data.get("states") or []