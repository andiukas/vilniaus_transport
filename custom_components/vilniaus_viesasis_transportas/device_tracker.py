import logging
import urllib.request
import time
from datetime import timedelta
from homeassistant.helpers.event import track_time_interval

_LOGGER = logging.getLogger(__name__)

URL = "https://www.stops.lt/vilnius/gps_full.txt"
UPDATE_INTERVAL = timedelta(seconds=30)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the device tracker platform from a config entry."""
    route = entry.data.get("route").upper()
    tracker = VilniusBusTracker(hass, route)
    
    # Naudojame šiek tiek kitokį metodą informuoti HA apie naujus įrenginius
    # legacy setup_scanner čia nebetinka, bet async_see vis dar veiks per hass.async_create_task
    track_time_interval(hass, tracker.update, UPDATE_INTERVAL)
    await tracker.update()

class VilniusBusTracker:
    def __init__(self, hass, route):
        self.hass = hass
        self.route = route
        self._active_entities = set()

    async def update(self, now=None):
        def fetch_data():
            timestamped_url = f"{URL}?t={int(time.time())}"
            req = urllib.request.Request(timestamped_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode("utf-8")

        try:
            # Vykdome tinklo užklausą neblokuojant HA gijos
            text = await self.hass.async_add_executor_job(fetch_data)
            lines = text.splitlines()
            current_batch = set()

            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6 and parts[1] == self.route:
                    masinos_nr = parts[3]
                    dev_id = f"vln_{self.route.lower()}_{masinos_nr}"
                    current_batch.add(dev_id)

                    # Naudojame hass.services, nes async_see legacy metoduose veikia kitaip
                    # Bet paprasčiausia toliau naudoti device_tracker.see servisą:
                    await self.hass.services.async_call(
                        "device_tracker", "see", {
                            "dev_id": dev_id,
                            "gps": [int(parts[5])/1000000, int(parts[4])/1000000],
                            "host_name": self.route,
                            "attributes": {
                                "friendly_name": f"{self.route} ({masinos_nr})",
                                "masinos_nr": masinos_nr,
                                "greitis": parts[6] if len(parts) > 6 else "0"
                            }
                        }
                    )
            
            # Neaktyvių valymas
            for old_id in self._active_entities - current_batch:
                await self.hass.services.async_call(
                    "device_tracker", "see", {"dev_id": old_id, "location_name": "not_home"}
                )
            self._active_entities = current_batch

        except Exception as e:
            _LOGGER.error("Klaida maršrutui %s: %s", self.route, e)
