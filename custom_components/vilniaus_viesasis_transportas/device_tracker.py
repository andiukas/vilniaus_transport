import logging
import urllib.request
import time
from datetime import timedelta

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

URL = "https://www.stops.lt/vilnius/gps_full.txt"
UPDATE_INTERVAL = timedelta(seconds=30)

async def async_setup_entry(hass, entry, async_add_entities):
    route = entry.data.get("route").upper()
    entity = VilniusBusTracker(route)
    async_add_entities([entity])
    async_track_time_interval(hass, entity.async_update, UPDATE_INTERVAL)


class VilniusBusTracker(TrackerEntity):
    def __init__(self, route):
        self._route = route
        self._attr_name = f"Vilnius {route}"
        self._attr_unique_id = f"vilnius_{route.lower()}"
        self._attr_latitude = None
        self._attr_longitude = None

    async def async_update(self, now=None):
        def fetch_data():
            timestamped_url = f"{URL}?t={int(time.time())}"
            req = urllib.request.Request(
                timestamped_url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode("utf-8")

        try:
            text = await self.hass.async_add_executor_job(fetch_data)
            lines = text.splitlines()

            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6 and parts[1] == self._route:
                    self._attr_latitude = int(parts[5]) / 1000000
                    self._attr_longitude = int(parts[4]) / 1000000
                    break

        except Exception as e:
            _LOGGER.error("Klaida maršrutui %s: %s", self._route, e)
