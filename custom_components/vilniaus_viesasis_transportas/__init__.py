"""Vilniaus viešasis transportas integracija."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# TURI SUTAPTI SU MANIFEST
DOMAIN = "vilniaus_viesasis_transportas"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Nustatome integraciją."""
    # Ši eilutė liepia HA užkrauti device_tracker.py
    await hass.config_entries.async_forward_entry_setups(entry, ["device_tracker"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ištriname integraciją."""
    return await hass.config_entries.async_unload_platforms(entry, ["device_tracker"])






