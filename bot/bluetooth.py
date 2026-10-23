import os
import subprocess

# read mac address. Preps for dynamic changing
def speaker() -> str:
    return os.environ["SPEAKER_MAC"]

def connected() -> bool:
    out = subprocess.run(["bluetoothctl", "info", speaker()], capture_output=True, text=True).stdout
    return "Connected: yes" in out

def connect() -> bool:
    try:
        subprocess.run(["bluetoothctl", "connect", speaker()], capture_output=True, timeout=20)
    except subprocess.TimeoutExpired:
        return False
    return connected()

def disconnect():
    subprocess.run(["bluetoothctl", "disconnect", speaker()], capture_output=True, timeout=20)
