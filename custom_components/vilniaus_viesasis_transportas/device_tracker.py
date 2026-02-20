import logging
import urllib.request
import time
import asyncio
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

URL = "https://www.stops.lt/vilnius/gps_full.txt"
UPDATE_INTERVAL = timedelta(seconds=30)
MAX_TRACKERS = 25 

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Ši funkcija iškviečiama iš __init__.py."""
    route = entry.data.get("route", "3G").upper()
    
    tracker = VilniusBusTracker(hass, route, entry)
    
    # Pradedame sekimą
    async_track_time_interval(hass, tracker.update_bus_data, UPDATE_INTERVAL)
    await tracker.update_bus_data()
    
    return True

class VilniusBusTracker:
    def __init__(self, hass, route, entry):
        self.hass = hass
        self.route = route
        self.entry = entry
        self._active_ids = set()

    async def update_bus_data(self, now=None):
        """Duomenų atnaujinimas."""
        try:
            text = await self.hass.async_add_executor_job(self._fetch_data)
            if not text: return

            lines = text.splitlines()
            found_buses = []

            for line in lines:
                if not line.strip(): continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6 and parts[1].upper() == self.route:
                    found_buses.append(parts)

            current_iteration_ids = set()

            for index in range(MAX_TRACKERS):
                dev_id = f"vln_{self.route.lower()}_{index + 1}"
                entity_id = f"device_tracker.{dev_id}"
                
                if index < len(found_buses):
                    bus = found_buses[index]
                    try:
                        lng = int(bus[4]) / 1_000_000
                        lat = int(bus[5]) / 1_000_000
                        
                        # Sukuriame/atnaujiname būseną
                        self.hass.states.async_set(
                            entity_id,
                            "home",
                            {
                                "latitude": lat,
                                "longitude": lng,
                                "source_type": "gps",
                                "gps_accuracy": 0,
                                "friendly_name": f"{self.route} autobusas #{index + 1}",
                                "icon": "mdi:bus",
                                "marsrutas": bus[1],
                                "masinos_nr": bus[3],
                                "reiso_id": bus[2]
                            }
                        )
                        current_iteration_ids.add(dev_id)
                    except: continue
                else:
                    if dev_id in self._active_ids:
                        self.hass.states.async_set(entity_id, "not_home", {"friendly_name": f"{self.route} (neaktyvus)"})

            self._active_ids = current_iteration_ids
        except Exception as e:
            _LOGGER.error("Klaida maršrutui %s: %s", self.route, e)

    def _fetch_data(self):
        try:
            timestamped_url = f"{URL}?t={int(time.time())}"
            req = urllib.request.Request(timestamped_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode("utf-8")
        except: return None
