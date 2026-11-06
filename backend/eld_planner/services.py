import requests
from datetime import datetime, timedelta

def geocode(location_str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': str(location_str).strip(),
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'FMCSA-ELD-Route-Planner/1.0 (contact@eldplanner.local)'
    }
    r = requests.get(url, params=params, headers=headers, timeout=10)
    if r.status_code != 200:
        raise ValueError(f"Geocoding service returned status {r.status_code}")
    data = r.json()
    if not data:
        raise ValueError(f"Could not locate address: {location_str}")
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


def split_timeline_into_days(timeline_events):
    days = []
    if not timeline_events:
        return days

    first_start = timeline_events[0]['start']
    current_day_date = first_start.date()
    day_start = datetime(current_day_date.year, current_day_date.month, current_day_date.day, 0, 0, 0)
    day_end = day_start + timedelta(days=1)

    while True:
        day_events = []
        for ev in timeline_events:
            s = max(ev['start'], day_start)
            e = min(ev['end'], day_end)
            if s < e:
                start_hour = (s - day_start).total_seconds() / 3600.0
                end_hour = (e - day_start).total_seconds() / 3600.0
                day_events.append({
                    'status': ev['status'],
                    'start_hour': round(start_hour, 2),
                    'end_hour': round(end_hour, 2),
                    'duration': round(end_hour - start_hour, 2),
                    'location': ev.get('location', '')
                })

        totals = {'OFF': 0.0, 'SB': 0.0, 'D': 0.0, 'ON': 0.0}
        for de in day_events:
            st = de['status']
            if st in totals:
                totals[st] = round(totals[st] + de['duration'], 2)

        days.append({
            'date': current_day_date.strftime("%Y-%m-%d"),
            'events': day_events,
            'totals': totals
        })

        if day_end >= timeline_events[-1]['end']:
            break

        current_day_date += timedelta(days=1)
        day_start = day_end
        day_end = day_start + timedelta(days=1)

    return days


def plan_eld_trip(current_loc, pickup_loc, dropoff_loc, cycle_used=0.0):
    start_lat, start_lon, start_name = geocode(current_loc)
    pickup_lat, pickup_lon, pickup_name = geocode(pickup_loc)
    drop_lat, drop_lon, drop_name = geocode(dropoff_loc)

    total_miles, drive_duration_hrs, geometry = get_osrm_route(
        (start_lat, start_lon),
        (pickup_lat, pickup_lon),
        (drop_lat, drop_lon)
    )

    t = datetime.now().replace(minute=0, second=0, microsecond=0)
    timeline = []

    # 1. Pre-trip inspection (On Duty)
    timeline.append({
        'status': 'ON',
        'start': t,
        'end': t + timedelta(minutes=30),
        'location': start_name
    })
    t += timedelta(minutes=30)

    # 2. Drive to pickup
    time_to_pickup = (drive_duration_hrs * 0.3)
    timeline.append({
        'status': 'D',
        'start': t,
        'end': t + timedelta(hours=time_to_pickup),
        'location': f"En route to {pickup_name}"
    })
    t += timedelta(hours=time_to_pickup)

    # 3. Loading at pickup (On Duty)
    timeline.append({
        'status': 'ON',
        'start': t,
        'end': t + timedelta(hours=1),
        'location': pickup_name
    })
    t += timedelta(hours=1)

    # 4. Main drive to dropoff with mandatory 30-min break
    remaining_drive = max(0.5, drive_duration_hrs * 0.7)
    first_leg = min(remaining_drive, 4.5)
    timeline.append({
        'status': 'D',
        'start': t,
        'end': t + timedelta(hours=first_leg),
        'location': "Highway transit"
    })
    t += timedelta(hours=first_leg)

    # Mandatory 30-min rest break
    timeline.append({
        'status': 'OFF',
        'start': t,
        'end': t + timedelta(minutes=30),
        'location': "Rest stop"
    })
    t += timedelta(minutes=30)

    # Second leg of driving
    second_leg = max(0.0, remaining_drive - first_leg)
    if second_leg > 0:
        timeline.append({
            'status': 'D',
            'start': t,
            'end': t + timedelta(hours=second_leg),
            'location': f"En route to {drop_name}"
        })
        t += timedelta(hours=second_leg)

    # 5. Unloading at dropoff (On Duty)
    timeline.append({
        'status': 'ON',
        'start': t,
        'end': t + timedelta(hours=1),
        'location': drop_name
    })
    t += timedelta(hours=1)

    # 6. Post-trip inspection & Off Duty
    timeline.append({
        'status': 'OFF',
        'start': t,
        'end': t + timedelta(hours=10),
        'location': drop_name
    })

    daily_logs = split_timeline_into_days(timeline)

    return {
        'total_miles': round(total_miles, 1),
        'total_driving_hours': round(drive_duration_hrs, 2),
        'cycle_remaining': max(0.0, round(70.0 - (float(cycle_used) + drive_duration_hrs), 2)),
        'route_geometry': geometry,
        'daily_logs': daily_logs,
        'stops': [
            {'type': 'start', 'name': start_name, 'lat': start_lat, 'lon': start_lon},
            {'type': 'pickup', 'name': pickup_name, 'lat': pickup_lat, 'lon': pickup_lon},
            {'type': 'dropoff', 'name': drop_name, 'lat': drop_lat, 'lon': drop_lon}
        ]
    }