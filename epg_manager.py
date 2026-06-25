import os
import re
import requests
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import shutil
import threading
import sys
import sqlite3

# Local cache for EPG
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
EPG_CACHE_DIR = os.path.join(script_dir, "epg_cache")

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

def normalize_name(name):
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r'\b(hd|sd|fhd|uhd|hevc|4k|1080p|720p)\b', '', name)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def get_db_conn():
    os.makedirs(EPG_CACHE_DIR, exist_ok=True)
    db_path = os.path.join(EPG_CACHE_DIR, "epg_cache.db")
    return sqlite3.connect(db_path)

def init_db():
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS programmes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT,
                start_time INTEGER,
                stop_time INTEGER,
                title TEXT,
                desc TEXT,
                UNIQUE(channel_id, start_time) ON CONFLICT IGNORE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_programmes_channel ON programmes(channel_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_programmes_start ON programmes(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_programmes_stop ON programmes(stop_time)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[-] Error initializing EPG database: {e}")

def cleanup_old_epg():
    try:
        now_ts = int(datetime.now().timestamp())
        cutoff = now_ts - 86400  # 24 hours ago
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM programmes WHERE stop_time < ?", (cutoff,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"[+] EPG Auto-cleanup: deleted {deleted_count} outdated programmes.")
    except Exception as e:
        print(f"[-] Error cleaning up old EPG: {e}")

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
        
    # Clean up old XML/GZ files in cache directory
    try:
        os.makedirs(EPG_CACHE_DIR, exist_ok=True)
        for f in os.listdir(EPG_CACHE_DIR):
            if f.endswith(".xml") or f.endswith(".gz"):
                try:
                    os.remove(os.path.join(EPG_CACHE_DIR, f))
                except Exception:
                    pass
    except Exception as e:
        print(f"[-] Error cleaning EPG cache directory: {e}")
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
    Loads and parses all XML files in the EPG cache directory and inserts them into SQLite.
    """
    if not os.path.exists(EPG_CACHE_DIR):
        return False
        
    try:
        cache_files = [os.path.join(EPG_CACHE_DIR, f) for f in os.listdir(EPG_CACHE_DIR) if f.endswith(".xml")]
    except Exception:
        return False
        
    if not cache_files:
        return False
        
    init_db()
    cleanup_old_epg()
    
    parsed_any = False
    for cache_file in cache_files:
        print(f"[*] Parsing EPG Cache file into SQLite: {os.path.basename(cache_file)}...")
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            
            # Performance tuning for SQLite batch operations
            cursor.execute("PRAGMA synchronous = OFF")
            cursor.execute("PRAGMA journal_mode = MEMORY")
            
            context = ET.iterparse(cache_file, events=('end',))
            batch = []
            
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
                        start_ts = int(start_dt.timestamp())
                        stop_ts = int(stop_dt.timestamp())
                        batch.append((channel, start_ts, stop_ts, title, desc))
                        
                        if len(batch) >= 1000:
                            cursor.executemany("""
                                INSERT OR IGNORE INTO programmes (channel_id, start_time, stop_time, title, desc)
                                VALUES (?, ?, ?, ?, ?)
                            """, batch)
                            batch = []
                            
                    elem.clear()
                elif elem.tag == 'channel':
                    elem.clear()
                    
            if batch:
                cursor.executemany("""
                    INSERT OR IGNORE INTO programmes (channel_id, start_time, stop_time, title, desc)
                    VALUES (?, ?, ?, ?, ?)
                """, batch)
                
            conn.commit()
            conn.close()
            parsed_any = True
        except Exception as e:
            print(f"[-] Error parsing EPG cache file {os.path.basename(cache_file)}: {e}")
            
    if parsed_any:
        print("[+] Loaded EPG data into SQLite cache successfully.")
        return True
        
    return False

def get_schedule(tvg_id, channel_name):
    """
    Returns the schedule list of dicts for a channel from SQLite.
    """
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get all unique channel IDs to execute matching algorithm
        cursor.execute("SELECT DISTINCT channel_id FROM programmes")
        db_channels = [r[0] for r in cursor.fetchall()]
        
        key = tvg_id if tvg_id in db_channels else None
        if not key:
            norm_channel = normalize_name(channel_name)
            if norm_channel:
                # 1. Exact match of normalized name
                for chan_id in db_channels:
                    if normalize_name(chan_id) == norm_channel:
                        key = chan_id
                        break
                
                # 2. Substring match of normalized name (avoid false matches with numeric suffixes)
                if not key:
                    for chan_id in db_channels:
                        norm_id = normalize_name(chan_id)
                        if norm_channel in norm_id or norm_id in norm_channel:
                            # Prevent false positives (e.g. VTV3 and VTV30)
                            m1 = re.search(r'\d+$', norm_channel)
                            m2 = re.search(r'\d+$', norm_id)
                            if m1 and m2 and m1.group() != m2.group():
                                continue
                            key = chan_id
                            break
                            
        if not key:
            conn.close()
            return []
            
        # Query programmes for the matched key
        cursor.execute("""
            SELECT start_time, stop_time, title, desc 
            FROM programmes 
            WHERE channel_id = ? 
            ORDER BY start_time ASC
        """, (key,))
        rows = cursor.fetchall()
        conn.close()
        
        schedule = []
        for r in rows:
            start_dt = datetime.fromtimestamp(r[0], tz=timezone.utc).astimezone()
            stop_dt = datetime.fromtimestamp(r[1], tz=timezone.utc).astimezone()
            schedule.append({
                'start': start_dt,
                'stop': stop_dt,
                'title': r[2],
                'desc': r[3]
            })
        return schedule
    except Exception as e:
        print(f"[-] Error querying schedule: {e}")
        return []

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

# Auto-initialize database when the module is imported
init_db()
