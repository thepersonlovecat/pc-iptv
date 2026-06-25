import os
import sys
import requests
import subprocess
import shutil

def find_7z_executable():
    # Check if 7z is on the PATH
    if shutil.which("7z"):
        return "7z"
        
    # Common locations on Windows
    common_paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
        r"C:\Program Files\3uTools9\extrastools\3uJailbreak\files\patchtools\7z-64\7z.exe",
        r"C:\Program Files\3uTools9\files\patchtools\7z-64\7z.exe"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
            
    # Search C:\Program Files for any 7z.exe as fallback
    try:
        search_dirs = [r"C:\Program Files", r"C:\Program Files (x86)"]
        for s_dir in search_dirs:
            if os.path.exists(s_dir):
                for root, dirs, files in os.walk(s_dir):
                    if "7z.exe" in files:
                        found_path = os.path.join(root, "7z.exe")
                        return found_path
    except Exception:
        pass
        
    return None

def download_and_extract_mpv_dll():
    target_dlls = ["mpv-1.dll", "mpv-2.dll", "libmpv-2.dll"]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if DLL already exists in script directory
    dll_found = False
    for dll in target_dlls:
        dll_path = os.path.join(script_dir, dll)
        if os.path.exists(dll_path):
            print(f"[+] Found {dll} in script directory: {dll_path}")
            dll_found = True
            
    if dll_found:
        print("[+] mpv DLLs already exist in script directory. Skipping download.")
        return True
            
    # Locate 7z.exe first
    exe_7z = find_7z_executable()
    if not exe_7z:
        print("[-] 7-Zip executable (7z.exe) not found on system.")
        print("[-] Please manually download the latest mpv-dev release from:")
        print("    https://github.com/zhongfly/mpv-winbuild/releases")
        print("    Extract the archive and copy 'libmpv-2.dll' or 'mpv-2.dll' to this folder:")
        print(f"    {script_dir}")
        return False
        
    print(f"[+] Found 7-Zip utility at: {exe_7z}")
    print("[*] Starting download process...")
    
    # Fetch release assets from GitHub API
    url = "https://api.github.com/repos/zhongfly/mpv-winbuild/releases/latest"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[-] Error fetching release info: {e}")
        return False
        
    download_url = None
    filename = None
    
    # Search for mpv-dev-x86_64-*.7z (excluding v3 for compatibility)
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if "mpv-dev-x86_64-" in name and "-v3-" not in name and name.endswith(".7z"):
            download_url = asset.get("browser_download_url")
            filename = name
            break
            
    if not download_url:
        # Fallback to any mpv-dev-x86_64
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if "mpv-dev-" in name and name.endswith(".7z"):
                download_url = asset.get("browser_download_url")
                filename = name
                break
                
    if not download_url:
        print("[-] Could not find a suitable mpv-dev 7z release asset.")
        return False
        
    archive_path = os.path.join(script_dir, filename)
    print(f"[*] Downloading {filename} to {archive_path}...")
    try:
        r = requests.get(download_url, stream=True, timeout=60)
        r.raise_for_status()
        with open(archive_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("[+] Download complete.")
    except Exception as e:
        print(f"[-] Error downloading file: {e}")
        if os.path.exists(archive_path):
            try:
                os.remove(archive_path)
            except:
                pass
        return False
        
    # Extract the DLL from the 7z archive using 7z.exe
    print("[*] Extracting DLL from archive using 7z.exe...")
    extracted_dll = None
    temp_extract_dir = os.path.join(script_dir, "temp_mpv_extract")
    
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
    os.makedirs(temp_extract_dir)
    
    try:
        # Run 7z.exe x archive_path -otemp_extract_dir -y
        cmd = [exe_7z, "x", archive_path, f"-o{temp_extract_dir}", "-y"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"[-] 7z.exe failed: {result.stderr}")
        else:
            print("[+] Extraction finished. Locating DLL...")
            # Walk through temp_extract_dir to find any of the target DLLs
            for root, dirs, files in os.walk(temp_extract_dir):
                for f_name in files:
                    if f_name.endswith(".dll") and ("mpv" in f_name or "libmpv" in f_name):
                        dll_path = os.path.join(root, f_name)
                        print(f"[+] Found library: {dll_path}")
                        
                        # Copy to script directory with multiple target names for safety
                        for target in target_dlls:
                            target_path = os.path.join(script_dir, target)
                            shutil.copy2(dll_path, target_path)
                            print(f"[+] Copied to {target_path}")
                        extracted_dll = f_name
                        break
                if extracted_dll:
                    break
    except Exception as e:
        print(f"[-] Error during extraction: {e}")
    finally:
        # Clean up downloaded 7z and temp folders
        if os.path.exists(archive_path):
            try:
                os.remove(archive_path)
            except Exception as e:
                print(f"[-] Could not delete archive file {archive_path}: {e}")
        if os.path.exists(temp_extract_dir):
            try:
                shutil.rmtree(temp_extract_dir)
            except Exception as e:
                print(f"[-] Could not delete temp folder: {e}")
            
    if extracted_dll:
        print("[+] Setup of mpv DLL completed successfully.")
        return True
    else:
        print("[-] Failed to extract any mpv DLL.")
        return False

if __name__ == "__main__":
    download_and_extract_mpv_dll()
