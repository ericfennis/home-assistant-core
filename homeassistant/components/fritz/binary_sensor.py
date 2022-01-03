"""AVM FRITZ!Box connectivity sensor."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .common import FritzBoxBaseEntity, FritzBoxTools
from .const import DOMAIN, MeshRoles

_LOGGER = logging.getLogger(__name__)


@dataclass
class FritzBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Fritz sensor entity."""

    exclude_mesh_role: MeshRoles = MeshRoles.SLAVE


SENSOR_TYPES: tuple[FritzBinarySensorEntityDescription, ...] = (
    FritzBinarySensorEntityDescription(
        key="is_connected",
        name="Connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FritzBinarySensorEntityDescription(
        key="is_linked",
        name="Link",
        device_class=BinarySensorDeviceClass.PLUG,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FritzBinarySensorEntityDescription(
        key="firmware_update",
        name="Firmware Update",
        device_class=BinarySensorDeviceClass.UPDATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        exclude_mesh_role=MeshRoles.NONE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up entry."""
    _LOGGER.debug("Setting up FRITZ!Box binary sensors")
    fritzbox_tools: FritzBoxTools = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FritzBoxBinarySensor(fritzbox_tools, entry.title, description)
        for description in SENSOR_TYPES
        if (description.exclude_mesh_role != fritzbox_tools.mesh_role)
    ]

    async_add_entities(entities, True)


class FritzBoxBinarySensor(FritzBoxBaseEntity, BinarySensorEntity):
    """Define FRITZ!Box connectivity class."""

    def __init__(
        self,
        fritzbox_tools: FritzBoxTools,
        device_friendly_name: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Init FRITZ!Box connectivity class."""
        self.entity_description = description
        self._attr_name = f"{device_friendly_name} {description.name}"
        self._attr_unique_id = f"{fritzbox_tools.unique_id}-{description.key}"
        super().__init__(fritzbox_tools, device_friendly_name)

    def update(self) -> None:
        """Update data."""
        _LOGGER.debug("Updating FRITZ!Box binary sensors")

        if self.entity_description.key == "firmware_update":
            self._attr_is_on = self._fritzbox_tools.update_available
            self._attr_extra_state_attributes = {
                "installed_version": self._fritzbox_tools.current_firmware,
                "latest_available_version": self._fritzbox_tools.latest_firmware,
            }
        if self.entity_description.key == "is_connected":
            self._attr_is_on = bool(self._fritzbox_tools.fritz_status.is_connected)
        elif self.entity_description.key == "is_linked":
            self._attr_is_on = bool(self._fritzbox_tools.fritz_status.is_linked)
