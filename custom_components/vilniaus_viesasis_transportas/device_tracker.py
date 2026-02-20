import logging
import urllib.request
import time
import asyncio
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.components.device_tracker import SOURCE_TYPE_GPS

_LOGGER = logging.getLogger(__name__)

URL = "https://www.stops.lt/vilnius/gps_full.txt"
UPDATE_INTERVAL = timedelta(seconds=30)
MAX_TRACKERS = 25 

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Nustatoma integracija iš Config Flow."""
    route = entry.data.get("route", "3G").upper()
    
    # Sukuriame trackerio valdytoją
    tracker = VilniusBusTracker(hass, route, entry)
    
    # Užregistruojame periodinį atnaujinimą
    async_track_time_interval(hass, tracker.update_bus_data, UPDATE_INTERVAL)
    
    # Paleidžiame pirmąjį atnaujinimą iškart
    await tracker.update_bus_data()
    
    return True

class VilniusBusTracker:
    def __init__(self, hass, route, entry):
        self.hass = hass
        self.route = route
        self.entry = entry
        self._active_ids = set()

    async def update_bus_data(self, now=None):
        """Pagrindinis duomenų gavimo ir esybių atnaujinimo ciklas."""
        try:
            # Naudojame executor, kad neužšaldytume HA pagrindinės gijos
            text = await self.hass.async_add_executor_job(self._fetch_data)
            if not text:
                _LOGGER.warning("Nepavyko gauti duomenų iš stops.lt maršrutui %s", self.route)
                return

            lines = text.splitlines()
            found_buses = []

            for line in lines:
                if not line.strip(): continue
                parts = [p.strip() for p in line.split(",")]
                
                # parts[1] yra maršruto numeris
                if len(parts) >= 6 and parts[1].upper() == self.route:
                    found_buses.append(parts)

            current_iteration_ids = set()

            for index in range(MAX_TRACKERS):
                # Unikalus ID kiekvienam autobuso lizdui (slot)
                dev_id = f"vln_{self.route.lower()}_{index + 1}"
                entity_id = f"device_tracker.{dev_id}"
                
                if index < len(found_buses):
                    bus = found_buses[index]
                    try:
                        lng = int(bus[4]) / 1_000_000
                        lat = int(bus[5]) / 1_000_000
                        
                        attrs = {
                            "marsrutas": str(bus[1]),
                            "reiso_id": str(bus[2]),
                            "masinos_nr": str(bus[3]),
                            "greitis": f"{bus[6]} km/h" if len(bus) > 6 else "0 km/h",
                            "statusas": "važiuoja",
                            "friendly_name": f"{self.route} autobusas #{index + 1}",
                            "icon": "mdi:bus",
                            "source_type": SOURCE_TYPE_GPS,
                            "gps_accuracy": 0,
                            "latitude": lat,
                            "longitude": lng,
                        }

                        # SVARBU: Naudojame async_set su integracijos nuoroda
                        self.hass.states.async_set(
                            entity_id,
                            "home",
                            attrs
                        )
                        current_iteration_ids.add(dev_id)
                    except (ValueError, IndexError):
                        continue
                else:
                    # Jei autobuso nebeliko (pvz. nuvažiavo į parką), nustatome 'not_home'
                    if dev_id in self._active_ids:
                        state = self.hass.states.get(entity_id)
                        old_attrs = dict(state.attributes) if state else {}
                        old_attrs["statusas"] = "neaktyvus"
                        
                        self.hass.states.async_set(
                            entity_id,
                            "not_home",
                            old_attrs
                        )

            self._active_ids = current_iteration_ids

        except Exception as e:
            _LOGGER.error("Kritinė klaida atnaujinant %s duomenis: %s", self.route, e)

    def _fetch_data(self):
        """Sinchroninis HTTP užklausos vykdymas."""
        try:
            timestamped_url = f"{URL}?t={int(time.time())}"
            req = urllib.request.Request(timestamped_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode("utf-8")
        except Exception as e:
            _LOGGER.error("Nepavyko pasiekti stops.lt: %s", e)
            return None
