import requests
from datetime import datetime, timedelta

def geocode(location_str):
    headers = {'User-Agent': 'eld-route-app/1.0'}
    url = f"https://nominatim.openstreetmap.org/search?q={location_str}&format=json&limit=1"
    
    r = requests.get(url, headers=headers)
    data = r.json()
    if not data:
        raise ValueError(f"Could not locate: {location_str}")
        
    return float(data[0]['lat']), float(data[0]['lon']), data[0]['display_name']

def get_osrm_route(start, pickup, drop):
    coords = f"{start[1]},{start[0]};{pickup[1]},{pickup[0]};{drop[1]},{drop[0]}"
    url = f"https://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"
    
    res = requests.get(url).json()
    if res.get('code') != 'Ok':
        raise Exception("Routing query failed via OSRM")
        
    route = res['routes'][0]
    miles = route['distance'] * 0.000621371
    duration_hrs = route['duration'] / 3600.0
    return miles, duration_hrs, route['geometry']

def plan_eld_trip(current_loc, pickup_loc, dropoff_loc, initial_cycle_used):
    start_lat, start_lon, s_name = geocode(current_loc)
    p_lat, p_lon, p_name = geocode(pickup_loc)
    d_lat, d_lon, d_name = geocode(dropoff_loc)

    total_miles, _, geom = get_osrm_route((start_lat, start_lon), (p_lat, p_lon), (d_lat, d_lon))

    avg_speed = 55.0
    drive_hours_needed = total_miles / avg_speed

    timeline = []
    current_time = datetime.now().replace(minute=0, second=0, microsecond=0)

    cycle_hours = float(initial_cycle_used)
    shift_driving = 0.0
    shift_window = 0.0
    since_break = 0.0
    miles_since_fuel = 0.0

    def record_event(status, duration, note, loc=""):
        nonlocal current_time, cycle_hours, shift_driving, shift_window, since_break
        start_dt = current_time
        end_dt = current_time + timedelta(hours=duration)

        timeline.append({
            'status': status,
            'start_iso': start_dt.isoformat(),
            'end_iso': end_dt.isoformat(),
            'hours': round(duration, 2),
            'remark': note,
            'location': loc
        })
        current_time = end_dt

        if status in ['D', 'ON']:
            cycle_hours += duration
            shift_window += duration
        elif status in ['OFF', 'SB'] and duration < 10.0:
            shift_window += duration

        if status == 'D':
            shift_driving += duration
            since_break += duration
        elif status in ['OFF', 'SB'] and duration >= 0.5:
            since_break = 0.0

    record_event('ON', 1.0, 'Pickup & Cargo Loading', p_name)

    remaining_drive = drive_hours_needed

    while remaining_drive > 0.05:
        if cycle_hours >= 70.0:
            record_event('OFF', 34.0, '34-hour restart (Cycle limit reached)')
            cycle_hours = 0.0
            shift_driving = 0.0
            shift_window = 0.0
            since_break = 0.0
            continue

        if shift_driving >= 11.0 or shift_window >= 14.0:
            record_event('OFF', 10.0, '10-hour rest break')
            shift_driving = 0.0
            shift_window = 0.0
            since_break = 0.0
            continue

        if since_break >= 8.0:
            record_event('OFF', 0.5, 'Mandatory 30-min rest break')
            continue

        max_chunk = min(
            remaining_drive,
            11.0 - shift_driving,
            14.0 - shift_window,
            8.0 - since_break,
            3.5
        )

        record_event('D', max_chunk, f'Driving ({round(max_chunk * avg_speed)} mi)')
        remaining_drive -= max_chunk
        miles_since_fuel += (max_chunk * avg_speed)

        if miles_since_fuel >= 1000.0 and remaining_drive > 0:
            record_event('ON', 0.5, 'Fueling Stop')
            miles_since_fuel = 0.0

    record_event('ON', 1.0, 'Drop-off & Unloading', d_name)
    record_event('OFF', 2.0, 'Post-trip inspection')

    sheets = split_timeline_into_days(timeline)

    return {
        'total_miles': round(total_miles, 1),
        'total_drive_hours': round(drive_hours_needed, 2),
        'route_geometry': geom,
        'log_sheets': sheets,
        'summary': {
            'start': s_name,
            'pickup': p_name,
            'dropoff': d_name,
            'total_days': len(sheets)
        }
    }

def split_timeline_into_days(timeline):
    sheets = []
    if not timeline:
        return sheets

    start_date = datetime.fromisoformat(timeline[0]['start_iso'])
    end_date = datetime.fromisoformat(timeline[-1]['end_iso'])
    day_cursor = start_date.replace(hour=0, minute=0, second=0)

    while day_cursor < end_date:
        next_day = day_cursor + timedelta(days=1)
        day_events = []
        sums = {'OFF': 0.0, 'SB': 0.0, 'D': 0.0, 'ON': 0.0}

        for ev in timeline:
            s = datetime.fromisoformat(ev['start_iso'])
            e = datetime.fromisoformat(ev['end_iso'])

            chunk_start = max(s, day_cursor)
            chunk_end = min(e, next_day)

            if chunk_end > chunk_start:
                duration = (chunk_end - chunk_start).total_seconds() / 3600.0
                st_hr = (chunk_start - day_cursor).total_seconds() / 3600.0
                end_hr = (chunk_end - day_cursor).total_seconds() / 3600.0

                sums[ev['status']] += duration
                day_events.append({
                    'status': ev['status'],
                    'start_hour': round(st_hr, 2),
                    'end_hour': round(end_hr, 2),
                    'duration': round(duration, 2),
                    'remark': ev['remark'],
                    'location': ev.get('location', '')
                })

        sheets.append({
            'date': day_cursor.strftime('%Y-%m-%d'),
            'totals': {k: round(v, 2) for k, v in sums.items()},
            'events': day_events
        })
        day_cursor = next_day

    return sheets
