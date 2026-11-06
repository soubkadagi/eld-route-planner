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