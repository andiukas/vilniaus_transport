from datetime import timedelta
import urllib.request
import logging
import time

from homeassistant.helpers.event import track_time_interval

_LOGGER = logging.getLogger(__name__)

# Pridedame laiko žymę prie URL, kad išvengtume duomenų kešavimo
URL = "https://www.stops.lt/vilnius/gps_full.txt"
ROUTE = "3G"
UPDATE_INTERVAL = timedelta(seconds=30)

def setup_scanner(hass, config, async_see, discovery_info=None):
    """Set up the Vilnius Bus device tracker."""
    VilniusBusTracker(hass, async_see)

class VilniusBusTracker:
    def __init__(self, hass, async_see):
        self.hass = hass
        self.async_see = async_see
        track_time_interval(hass, self.update, UPDATE_INTERVAL)
        self.update()

    def update(self, now=None):
        """Fetch and update all buses with cache prevention."""
        try:
            # Pridedame unikalų skaičių prie URL (pvz. ?t=123456789), 
            # kad serveris neduotų pasenusio failo
            timestamped_url = f"{URL}?t={int(time.time())}"
            
            req = urllib.request.Request(
                timestamped_url, 
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Pragma': 'no-cache',
                    'Cache-Control': 'no-cache'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                text = response.read().decode("utf-8")

            lines = text.splitlines()
            found_ids = [] # Sekti, ką radome šiame cikle
            
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                
                # Pagal tavo nurodytą struktūrą:
                # 0: Transportas, 1: Marsrutas, 2: ReisoID, 3: MasinosNumeris, 4: Lng, 5: Lat
                if len(parts) < 6:
                    continue

                route_num = parts[1]
                if route_num != ROUTE:
                    continue

                reiso_id = parts[2]
                masinos_nr = parts[3]
                
                try:
                    longitude = int(parts[4]) / 1_000_000
                    latitude = int(parts[5]) / 1_000_000
                except (ValueError, IndexError):
                    continue

                # Sukuriame unikalų ID
                dev_id = f"vln_3g_{reiso_id}"
                display_name = f"Autobusai {route_num} {reiso_id}"

                # Atnaujiname HA
                self.async_see(
                    dev_id=dev_id,
                    host_name=display_name,
                    gps=(latitude, longitude),
                    source_type="gps",
                    attributes={
                        "reiso_id": reiso_id,
                        "masinos_numeris": masinos_nr,
                        "route": route_num,
                        "last_update": time.strftime("%H:%M:%S")
                    }
                )
                found_ids.append(dev_id)

            _LOGGER.debug("Rasta 3G autobusų: %s", len(found_ids))

        except Exception as e:
            _LOGGER.error("Klaida gaunant 3G duomenis: %s", e)