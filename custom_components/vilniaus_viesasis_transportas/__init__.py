"""Vilniaus viešasis transportas integracija."""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

DOMAIN = "vilniaus_viesasis_transportas"
PLATFORMS = ["device_tracker"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Nustatoma integracija iš Config Entry."""
    _LOGGER.info("Kraunama Vilniaus transporto integracija maršrutui: %s", entry.data.get("route"))
    
    # Ši eilutė užregistruoja platformas (mūsų atveju device_tracker)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ištrinama integracija."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok




