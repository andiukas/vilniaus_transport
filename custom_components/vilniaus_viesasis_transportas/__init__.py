"""Vilniaus viešasis transportas integracija."""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

# PATAISYTA: Turi sutapti su manifest.json domain lauku
DOMAIN = "vilniaus_viesasis_transportas"
PLATFORMS = ["device_tracker"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Vilnius Transport from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)



