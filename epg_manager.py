import os
import re
import requests
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import shutil
import threading

# Local cache for EPG
import sys
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
EPG_CACHE_DIR = os.path.join(script_dir, "epg_cache")
EPG_DATA = {} # channel_id/name -> list of programmes
epg_lock = threading.Lock()

def parse_xmltv_time(time_str):
    """
    Parses XMLTV time format: '20260622030000 +0700' or '20260622030000'
    Returns a datetime object in local time.
    """
    if not time_str:
        return None
    try:
        # Match time part and timezone part
        m = re.match(r"(\d{14})(?:\s+([+-]\d{4}))?", time_str)
        if not m:
            return None
        dt_str, tz_offset = m.groups()
        dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
        
        if tz_offset:
            # Parse offset like +0700
            sign = 1 if tz_offset[0] == '+' else -1
            hours = int(tz_offset[1:3])
            minutes = int(tz_offset[3:5])
            tz = timezone(timedelta(hours=sign*hours, minutes=sign*minutes))
            dt = dt.replace(tzinfo=tz)
            # Convert to local timezone
            return dt.astimezone()
        else:
            # Assume UTC or local
            return dt.replace(tzinfo=timezone.utc).astimezone()
    except Exception as e:
        print(f"Error parsing time {time_str}: {e}")
        return None

def download_epg(url):
    """
    Downloads EPG XML/GZ file(s) in a background friendly way.
    Supports comma-separated URLs.
    """
    if not url:
        return False
        
    urls = [u.strip() for u in url.split(",") if u.strip()]
    if not urls:
        return False
        
    # Re-create clean cache directory
    try:
        if os.path.exists(EPG_CACHE_DIR):
            shutil.rmtree(EPG_CACHE_DIR)
        os.makedirs(EPG_CACHE_DIR, exist_ok=True)
    except Exception as e:
        print(f"[-] Error creating EPG cache directory: {e}")
        return False
        
    headers = {
        "User-Agent": "VLC/3.0.18 LibVLC/3.0.18"
    }
    
    success_count = 0
    for i, u in enumerate(urls):
        try:
            print(f"[*] Downloading EPG ({i+1}/{len(urls)}) from {u}...")
            r = requests.get(u, headers=headers, timeout=20, stream=True)
            r.raise_for_status()
            
            # Check if gzipped
            is_gzip = u.lower().endswith(".gz") or r.headers.get('Content-Encoding') == 'gzip' or "gzip" in r.headers.get('Content-Type', '').lower()
            
            cache_file = os.path.join(EPG_CACHE_DIR, f"cache_{i}.xml")
            with open(cache_file, "wb") as f:
                if is_gzip:
                    with gzip.GzipFile(fileobj=r.raw) as gz:
                        shutil.copyfileobj(gz, f)
                else:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"[+] Downloaded and cached EPG source {i+1}")
            success_count += 1
        except Exception as e:
            print(f"[-] Failed downloading EPG from {u}: {e}")
            
    return success_count > 0

def load_epg_cache():
    """
    Loads and parses all files in the EPG cache directory.
    Uses thread-safe temporary storage to avoid race conditions.
    """
    global EPG_DATA
    
    if not os.path.exists(EPG_CACHE_DIR):
        return False
        
    try:
        cache_files = [os.path.join(EPG_CACHE_DIR, f) for f in os.listdir(EPG_CACHE_DIR) if f.endswith(".xml")]
    except Exception:
        return False
        
    if not cache_files:
        return False
        
    temp_epg_data = {}
    parsed_any = False
    for cache_file in cache_files:
        print(f"[*] Parsing EPG Cache file: {os.path.basename(cache_file)}...")
        try:
            context = ET.iterparse(cache_file, events=('end',))
            for event, elem in context:
                if elem.tag == 'programme':
                    channel = elem.get('channel')
                    start_str = elem.get('start')
                    stop_str = elem.get('stop')
                    
                    title_elem = elem.find('title')
                    title = title_elem.text if title_elem is not None else "No Title"
                    
                    desc_elem = elem.find('desc')
                    desc = desc_elem.text if desc_elem is not None else ""
                    
                    start_dt = parse_xmltv_time(start_str)
                    stop_dt = parse_xmltv_time(stop_str)
                    
                    if channel and start_dt and stop_dt:
                        prog = {
                            'start': start_dt,
                            'stop': stop_dt,
                            'title': title,
                            'desc': desc
                        }
                        if channel not in temp_epg_data:
                            temp_epg_data[channel] = []
                        temp_epg_data[channel].append(prog)
                    
                    elem.clear()
                elif elem.tag == 'channel':
                    elem.clear()
            parsed_any = True
        except Exception as e:
            print(f"[-] Error parsing EPG cache file {os.path.basename(cache_file)}: {e}")
            
    if parsed_any:
        # Sort programmes by start time
        for channel in temp_epg_data:
            temp_epg_data[channel].sort(key=lambda x: x['start'])
            
        # Thread-safe pointer assignment
        with epg_lock:
            EPG_DATA = temp_epg_data
            
        print(f"[+] Loaded EPG data for {len(temp_epg_data)} channels from all sources.")
        return True
        
    return False

def get_schedule(tvg_id, channel_name):
    """
    Returns the schedule list of dicts for a channel.
    Uses a shallow copy to prevent size modifications during iteration.
    """
    with epg_lock:
        local_epg_data = EPG_DATA.copy()
        
    key = tvg_id if tvg_id in local_epg_data else None
    if not key:
        # Try matching by name
        for chan_id in local_epg_data:
            if channel_name.lower().strip() in chan_id.lower() or chan_id.lower() in channel_name.lower():
                key = chan_id
                break
                
    if not key:
        return []
        
    return local_epg_data[key]

def get_current_program(tvg_id, channel_name):
    """
    Returns the current active program dict or None.
    """
    schedule = get_schedule(tvg_id, channel_name)
    if not schedule:
        return None
        
    now = datetime.now().astimezone()
    for prog in schedule:
        if prog['start'] <= now <= prog['stop']:
            return prog
            
    return None
