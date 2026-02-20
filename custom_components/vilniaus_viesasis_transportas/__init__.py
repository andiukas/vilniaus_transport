"""Vilniaus viešasis transportas integracija."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# TURI sutapti su manifest.json "domain"
DOMAIN = "vilniaus_viesasis_transportas"
PLATFORMS = ["device_tracker"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Nustatoma integracija iš Config Entry."""
    # Ši eilutė perduoda valdymą į device_tracker.py
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ištrinama integracija (kai vartotojas paspaudžia Delete)."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)





