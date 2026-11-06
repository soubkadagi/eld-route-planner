import requests
from datetime import datetime, timedelta

def geocode(location_str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': location_str.strip(),
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'FMCSA-ELD-Planner-App/1.0 (test-contact@example.com)'
    }
    
    r = requests.get(url, params=params, headers=headers, timeout=10)
    
    if r.status_code != 200:
        raise ValueError(f"Geocoding service returned status {r.status_code}")
        
    data = r.json()
    if not data or len(data) == 0:
        raise ValueError(f"Could not locate: {location_str}")
        
    return float(data[0]['lat']), float(data[0]['lon']), data[0]['display_name']

def get_osrm_route(start, pickup, drop):
    coords = f"{start[1]},{start[0]};{pickup[1]},{pickup[0]};{drop[1]},{drop[0]}"
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
    
    res = requests.get(url, timeout=15)
    if res.status_code != 200:
        raise Exception("Routing service unavailable")
        
    data = res.json()
    if data.get('code') != 'Ok':
        raise Exception("Routing query failed via OSRM")
        
    route = data['routes'][0]
    miles = route['distance'] * 0.000621371
    duration_hrs = route['duration'] / 3600.0
    return miles, duration_hrs, route['geometry']