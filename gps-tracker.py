
import time
import json
print(f"🗺️ GPS Tracker App started on device: device-3")
coords = [(52.5200, 13.4050), (52.5201, 13.4051), (52.5202, 13.4052)]
for lat, lon in coords:
    print(f"📍 Location: {lat}, {lon}")
    time.sleep(1)
print("✅ GPS Tracker App completed successfully")
