import re
import requests

def parse_m3u(file_path_or_url):
    """
    Parses an M3U playlist file or URL.
    Returns a list of dicts: [{'name': ..., 'url': ..., 'logo': ..., 'group': ..., 'tvg-id': ...}]
    """
    channels = []
    content = ""
    epg_url = None
    
    # Simple holder for extracted EPG url to return metadata along with channels
    # We will return a tuple (channels, epg_url) instead, or check the header line.
    
    if file_path_or_url.startswith("http://") or file_path_or_url.startswith("https://"):
        try:
            # Set VLC User-Agent to match standard IPTV player requests
            headers = {
                "User-Agent": "VLC/3.0.18 LibVLC/3.0.18"
            }
            r = requests.get(file_path_or_url, headers=headers, timeout=15)
            r.raise_for_status()
            content = r.text
        except Exception as e:
            print(f"Error fetching remote playlist: {e}")
            return [], None
    else:
        try:
            with open(file_path_or_url, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading local playlist: {e}")
            return [], None
            
    # Parse lines
    lines = content.splitlines()
    current_channel = {}
    
    # Regular expressions for attributes
    logo_regex = re.compile(r'tvg-logo=["\']([^"\']+)["\']', re.IGNORECASE)
    group_regex = re.compile(r'group-title=["\']([^"\']+)["\']', re.IGNORECASE)
    id_regex = re.compile(r'tvg-id=["\']([^"\']+)["\']', re.IGNORECASE)
    
    # EPG URL extraction regex
    epg_regex = re.compile(r'(?:url-tvg|x-tvg-url|tvg-url)=["\']?([^"\',\s]+)["\']?', re.IGNORECASE)
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("#EXTM3U"):
            epg_match = epg_regex.search(line)
            if epg_match:
                epg_url = epg_match.group(1)
                
        elif line.startswith("#EXTINF:"):
            current_channel = {}
            # Extract channel name (everything after the last comma)
            name_parts = line.split(",", 1)
            name = name_parts[1].strip() if len(name_parts) > 1 else "Unknown Channel"
            current_channel["name"] = name
            
            # Extract attributes
            logo_match = logo_regex.search(line)
            current_channel["logo"] = logo_match.group(1) if logo_match else ""
            
            group_match = group_regex.search(line)
            current_channel["group"] = group_match.group(1) if group_match else "Default"
            
            id_match = id_regex.search(line)
            current_channel["tvg-id"] = id_match.group(1) if id_match else ""
            
        elif line.startswith("#"):
            continue
        else:
            # This is the stream URL
            if current_channel and "name" in current_channel:
                current_channel["url"] = line
                channels.append(current_channel)
                current_channel = {}
                
    return channels, epg_url
