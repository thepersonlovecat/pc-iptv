import os
import json
import sys

if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(script_dir, "config.json")

DEFAULT_CONFIG = {
    "playlists": [
        {
            "name": "Default Playlist",
            "url": "playlist.m3u",
            "is_local": True
        }
    ],
    "favorites": [],
    "history": [],
    "active_playlist_url": "playlist.m3u"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
        
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Ensure all keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")

def add_favorite(channel_name, stream_url):
    config = load_config()
    fav_item = {"name": channel_name, "url": stream_url}
    if fav_item not in config["favorites"]:
        config["favorites"].append(fav_item)
        save_config(config)
        return True
    return False

def remove_favorite(stream_url):
    config = load_config()
    initial_len = len(config["favorites"])
    config["favorites"] = [f for f in config["favorites"] if f["url"] != stream_url]
    if len(config["favorites"]) < initial_len:
        save_config(config)
        return True
    return False

def is_favorite(stream_url):
    config = load_config()
    for f in config["favorites"]:
        if f["url"] == stream_url:
            return True
    return False

def add_history(channel_name, stream_url):
    config = load_config()
    history_item = {"name": channel_name, "url": stream_url}
    
    # Remove if already exists to move to top
    config["history"] = [h for h in config["history"] if h["url"] != stream_url]
    
    # Insert at top
    config["history"].insert(0, history_item)
    
    # Limit to 20 items
    config["history"] = config["history"][:20]
    save_config(config)