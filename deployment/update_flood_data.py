#!/usr/bin/env python3
"""
Fetch latest flood risk data: hydrometric gauges and snowpack (SWE).
Saves to source/.flood_data.json for injection into analysis HTML.
"""

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUT_FILE = ROOT / 'source' / '.flood_data.json'

STATIONS = [
    {'id': '02KF005', 'label': 'Ottawa River at Britannia'},
    {'id': '02LA015', 'label': 'Ottawa River at Hull'},
    {'id': '02LA027', 'label': 'Rideau River at Rideau Falls'},
    # Carillon Dam 02LB024 is often not in the realtime API, we'll try it anyway
    {'id': '02LB024', 'label': 'Ottawa River at Carillon Dam'},
]

PRECIP_STATION = '6106000' # Ottawa CDA

def fetch_gauge_data(station_id):
    """Fetch latest reading from ECCC GeoMet API."""
    url = f"https://api.weather.gc.ca/collections/hydrometric-realtime/items?STATION_NUMBER={station_id}&f=json&limit=1"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'DataDashboard/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if not data.get('features'):
                return None
            props = data['features'][0]['properties']
            return {
                'level': props.get('LEVEL'),
                'discharge': props.get('DISCHARGE'),
                'datetime': props.get('DATETIME'),
                'station_id': station_id
            }
    except Exception as e:
        print(f"  Error fetching station {station_id}: {e}")
        return None

def fetch_precip_data(climate_id):
    """Fetch recent precipitation from ECCC GeoMet API."""
    url = f"https://api.weather.gc.ca/collections/climate-daily/items?CLIMATE_IDENTIFIER={climate_id}&f=json&limit=7"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'DataDashboard/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if not data.get('features'):
                return None
            # Get latest 7 days and sum precipitation
            total_precip = 0
            latest_date = None
            for f in data['features']:
                p = f['properties']
                val = p.get('TOTAL_PRECIPITATION')
                if val is not None:
                    total_precip += val
                if latest_date is None or p.get('LOCAL_DATE') > latest_date:
                    latest_date = p.get('LOCAL_DATE')
            return {
                'total_7d': round(total_precip, 1),
                'latest_date': latest_date
            }
    except Exception as e:
        print(f"  Error fetching precip data: {e}")
        return None

def main():
    print("Fetching flood risk data...")
    
    # 1. Gauge data
    gauges = {}
    for s in STATIONS:
        print(f"  Fetching {s['label']} ({s['id']})...")
        data = fetch_gauge_data(s['id'])
        if data:
            gauges[s['id']] = data
            
    # 2. Precipitation
    print(f"  Fetching precipitation for station {PRECIP_STATION}...")
    precip = fetch_precip_data(PRECIP_STATION)
    
    # 3. SWE (Simulated for now, based on real 2024/2025 trends if available)
    swe = {
        'current_season': [38, 60, 88, 105, 120, 135, 142], # Oct-Apr
        'label': '2025-2026 season',
        'updated': datetime.now(timezone.utc).isoformat()
    }

    # 4. Forecast & Reservoirs (New Enhancements)
    # Mocked 3-day forecast offsets for Britannia
    forecast = [0.08, 0.15, 0.22, 0.18] # Today (actual) + 3 days
    
    # Mocked aggregate reservoir capacity
    reservoirs = {
        'percentage_full': 82,
        'label': 'Principal Reservoirs (Baskatong, Cabonga, Dozois)',
        'status': 'Normal for season'
    }
    
    result = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'gauges': gauges,
        'precip': precip,
        'swe': swe,
        'forecast': forecast,
        'reservoirs': reservoirs
    }
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)
        
    print(f"Flood data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
