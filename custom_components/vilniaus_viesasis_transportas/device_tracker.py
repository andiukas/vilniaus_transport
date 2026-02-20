import logging
import urllib.request
import time
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)
URL = "https://www.stops.lt/vilnius/gps_full.txt"

async def async_setup_entry(hass, entry, async_add_entities):
    """Ši funkcija paleidžiama, kai HA krauna device_tracker platformą."""
    route = entry.data.get("route", "3G").upper()
    
    # Sukuriame valdytoją, kuris tiesiogiai atnaujins būsenas
    tracker_manager = VilniusTrackerManager(hass, route)
    
    async_track_time_interval(hass, tracker_manager.update_data, timedelta(seconds=30))
    await tracker_manager.update_data()
    
    return True

class VilniusTrackerManager:
    def __init__(self, hass, route):
        self.hass = hass
        self.route = route

    async def update_data(self, now=None):
        try:
            # Duomenų gavimas
            text = await self.hass.async_add_executor_job(self._fetch)
            if not text: return

            lines = text.splitlines()
            found = [l.split(",") for l in lines if len(l.split(",")) >= 6 and l.split(",")[1].upper() == self.route]

            for i in range(15): # Stebime iki 15 autobusų
                dev_id = f"vln_{self.route.lower()}_{i+1}"
                if i < len(found):
                    bus = found[i]
                    self.hass.states.async_set(
                        f"device_tracker.{dev_id}",
                        "home",
                        {
                            "latitude": int(bus[5])/1000000,
                            "longitude": int(bus[4])/1000000,
                            "source_type": "gps",
                            "friendly_name": f"{self.route} Autobusas {i+1}",
                            "icon": "mdi:bus",
                            "masinos_nr": bus[3]
                        }
                    )
                else:
                    # Jei autobuso nėra, bet esybė egzistuoja - pažymime, kad nebevažiuoja
                    state = self.hass.states.get(f"device_tracker.{dev_id}")
                    if state and state.state != "not_home":
                        self.hass.states.async_set(f"device_tracker.{dev_id}", "not_home", state.attributes)
        except Exception as e:
            _LOGGER.error("Klaida: %s", e)

    def _fetch(self):
        req = urllib.request.Request(f"{URL}?t={int(time.time())}", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.read().decode("utf-8")
