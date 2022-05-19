"""Support for MYHome covers, with timed option"""
import logging

import voluptuous as vol

from datetime import timedelta

from homeassistant.core import callback
from homeassistant.helpers import entity_platform
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    PLATFORM_SCHEMA,
    DOMAIN as PLATFORM,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
    CoverDeviceClass,
    CoverEntity,
)

from homeassistant.const import (
    CONF_NAME,
    CONF_DEVICES,
    CONF_ENTITIES,
    #These may as well be useless depending on how this integration will work
    ATTR_ENTITY_ID,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_STOP_COVER,
)

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

from OWNd.message import (
    OWNAutomationEvent,
    OWNAutomationCommand,
)

from .const import (
    CONF,
    CONF_GATEWAY,
    CONF_WHO,
    CONF_WHERE,
    CONF_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_ADVANCED_SHUTTER,
    DOMAIN,
    CONF_TIMED,
    CONF_TRAVELLING_TIME_DOWN,
    CONF_TRAVELLING_TIME_UP,
    CONF_SEND_STOP_AT_ENDS,
    DEFAULT_ADVANCED,
    ATTR_ACTION,
    ATTR_POSITION_TYPE,
    ATTR_POSITION_TYPE_CURRENT,
    ATTR_POSITION_TYPE_TARGET,
    ATTR_UNCONFIRMED_STATE,
    SERVICE_SET_KNOWN_POSITION,
    SERVICE_SET_KNOWN_ACTION,
    DEFAULT_TIMED,
    DEFAULT_TRAVEL_TIME,
    DEFAULT_SEND_STOP_AT_ENDS,
)

from .myhome_device import MyHOMEEntity
from .gateway import MyHOMEGatewayHandler

MYHOME_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_WHERE): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_TIMED, default=DEFAULT_TIMED): cv.boolean,
        vol.Optional(CONF_TRAVELLING_TIME_DOWN, default=DEFAULT_TRAVEL_TIME): cv.positive_int,
        vol.Optional(CONF_TRAVELLING_TIME_UP, default=DEFAULT_TRAVEL_TIME): cv.positive_int,
        vol.Optional(CONF_SEND_STOP_AT_ENDS, default=DEFAULT_SEND_STOP_AT_ENDS): cv.boolean,
        vol.Optional(CONF_ADVANCED_SHUTTER, default=DEFAULT_ADVANCED): cv.boolean,
        vol.Optional(CONF_MANUFACTURER): cv.string,
        vol.Optional(CONF_DEVICE_MODEL): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_DEVICES, default={}): cv.schema_with_slug_keys(MYHOME_SCHEMA)}
)

POSITION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required(ATTR_POSITION): cv.positive_int,
        vol.Optional(ATTR_POSITION_TYPE, default=ATTR_POSITION_TYPE_TARGET): cv.string
    }
)

ACTION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required(ATTR_ACTION): cv.string
    }
)

async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    if CONF not in hass.data[DOMAIN]:
        return False
    hass.data[DOMAIN][CONF][PLATFORM] = {}
    _configured_covers = config.get(CONF_DEVICES)

    if _configured_covers:
        for _, entity_info in _configured_covers.items():
            who = "2"
            where = entity_info[CONF_WHERE]
            device_id = f"{who}-{where}"
            name = (
                entity_info[CONF_NAME]
                if CONF_NAME in entity_info
                else f"A{where[:len(where)//2]}PL{where[len(where)//2:]}"
            )
            travel_time_down = [CONF_TRAVELLING_TIME_DOWN]
            travel_time_up = [CONF_TRAVELLING_TIME_UP]
            timed = entity_info[CONF_TIMED]
            send_stop_at_ends = [CONF_SEND_STOP_AT_ENDS]
            advanced = entity_info[CONF_ADVANCED_SHUTTER]
            entities = []
            manufacturer = (
                entity_info[CONF_MANUFACTURER]
                if CONF_MANUFACTURER in entity_info
                else None
            )
            model = (
                entity_info[CONF_DEVICE_MODEL]
                if CONF_DEVICE_MODEL in entity_info
                else None
            )
            hass.data[DOMAIN][CONF][PLATFORM][device_id] = {
                CONF_WHO: who,
                CONF_WHERE: where,
                CONF_ENTITIES: entities,
                CONF_NAME: name,
                CONF_TIMED: timed,
                CONF_TRAVELLING_TIME_DOWN: travel_time_down,
                CONF_TRAVELLING_TIME_UP: travel_time_up,
                CONF_SEND_STOP_AT_ENDS: send_stop_at_ends,
                CONF_ADVANCED_SHUTTER: advanced,
                CONF_MANUFACTURER: manufacturer,
                CONF_DEVICE_MODEL: model,
            }

            platform = entity_platform.current_platform.get()

            platform.async_register_entity_service(
                SERVICE_SET_KNOWN_POSITION, POSITION_SCHEMA, "set_known_position"
            )

            platform.async_register_entity_service(
                SERVICE_SET_KNOWN_ACTION, ACTION_SCHEMA, "set_known_action"
            )

async def async_setup_entry(
    hass, config_entry, async_add_entities
):  # pylint: disable=unused-argument
    if PLATFORM not in hass.data[DOMAIN][CONF]:
        return True

    _covers = []
    _configured_covers = hass.data[DOMAIN][CONF][PLATFORM]

    for _cover in _configured_covers.keys():
        _cover = MyHOMECover(
            hass=hass,
            device_id=_cover,
            who=_configured_covers[_cover][CONF_WHO],
            where=_configured_covers[_cover][CONF_WHERE],
            name=_configured_covers[_cover][CONF_NAME],
            timed=_configured_covers[_cover][CONF_TIMED],
            travel_time_down=_configured_covers[_cover][CONF_TRAVELLING_TIME_DOWN],
            travel_time_up=_configured_covers[_cover][CONF_TRAVELLING_TIME_UP],
            send_stop_at_ends=_configured_covers[_cover][CONF_SEND_STOP_AT_ENDS],
            advanced=_configured_covers[_cover][CONF_ADVANCED_SHUTTER],
            manufacturer=_configured_covers[_cover][CONF_MANUFACTURER],
            model=_configured_covers[_cover][CONF_DEVICE_MODEL],
            gateway=hass.data[DOMAIN][CONF_GATEWAY],
        )
        _covers.append(_cover)

    async_add_entities(_covers)

async def async_unload_entry(hass, config_entry):  # pylint: disable=unused-argument
    if PLATFORM not in hass.data[DOMAIN][CONF]:
        return True

    _configured_covers = hass.data[DOMAIN][CONF][PLATFORM]

    for _cover in _configured_covers.keys():
        del hass.data[DOMAIN][CONF_ENTITIES][_cover]

class MyHOMECover(MyHOMEEntity, CoverEntity):

    device_class = CoverDeviceClass.SHUTTER

    def __init__(
        self,
        hass,
        name: str,
        device_id: str,
        who: str,
        where: str,
        timed: bool,
        travel_time_down: int,
        travel_time_up: int,
        send_stop_at_ends: bool,
        advanced: bool,
        manufacturer: str,
        model: str,
        gateway: MyHOMEGatewayHandler,
    ):
        super().__init__(
            hass=hass,
            name=name,
            device_id=device_id,
            who=who,
            where=where,
            manufacturer=manufacturer,
            model=model,
            gateway=gateway,
        )
        from xknx.devices import TravelCalculator

        self._attr_supported_features = SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP
        if advanced:
            self._attr_supported_features |= SUPPORT_SET_POSITION
        if timed:
            self._attr_supported_features |= SUPPORT_SET_POSITION
            self._travel_time_down = travel_time_down
            self._travel_time_up = travel_time_up
            self._send_stop_at_ends = send_stop_at_ends
            self._assume_uncertain_position = True
            self._target_position = 0
            self._processing_known_position = False
            self.tc = TravelCalculator(self._travel_time_down, self._travel_time_up)

        self._gateway_handler = gateway

        self._attr_extra_state_attributes = {
            "A": where[: len(where) // 2],
            "PL": where[len(where) // 2 :],
        }



        self._attr_current_cover_position = None
        self._attr_is_opening = None
        self._attr_is_closing = None
        self._attr_is_closed = None

    async def async_added_to_hass(self):
        """ Only cover position and confidence in that matters."""
        """ The rest is calculated from this attribute.        """
        old_state = await self.async_get_last_state()
        _LOGGER.debug(self._name + ': ' + 'async_added_to_hass :: oldState %s', old_state)
        if (old_state is not None and self.tc is not None and old_state.attributes.get(ATTR_CURRENT_POSITION) is not None):
            self.tc.set_position(int(old_state.attributes.get(ATTR_CURRENT_POSITION)))
        if (old_state is not None and old_state.attributes.get(ATTR_UNCONFIRMED_STATE) is not None and not self._always_confident):
            if type(old_state.attributes.get(ATTR_UNCONFIRMED_STATE)) == bool:
                self._assume_uncertain_position = old_state.attributes.get(ATTR_UNCONFIRMED_STATE)
        else:
            self._assume_uncertain_position = str(old_state.attributes.get(ATTR_UNCONFIRMED_STATE)) == str(True)

    async def async_update(self):
        """
        Update the entity.

        Only used by the generic entity update service.
        """
        await self._gateway_handler.send_status_request(
                OWNAutomationCommand.status(self._where)
        )

    async def _handle_stop(self, **kwargs):  # pylint: disable=unused-argument
        """Stop the cover."""
        await self._gateway_handler.send(OWNAutomationCommand.stop_shutter(self._where))
        if self.tc.is_traveling():
            _LOGGER.debug(self._name + ': ' + '_handle_stop :: button stops cover')
            self.tc.stop()
            self.stop_auto_updater()

    @property
    def unconfirmed_state(self):
        """Return the assume state as a string to persist through restarts ."""
        return str(self._assume_uncertain_position)
    @property
    def name(self):
        """Return the name of the cover."""
        return self._name
    @property
    def device_class(self):
        """Return the device class of the cover."""
        return self._device_class
    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        attr = {}
        if self._travel_time_down is not None:
            attr[CONF_TRAVELLING_TIME_DOWN] = self._travel_time_down
        if self._travel_time_up is not None:
            attr[CONF_TRAVELLING_TIME_UP] = self._travel_time_up 
        attr[ATTR_UNCONFIRMED_STATE] = str(self._assume_uncertain_position)
        return attr
    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return self.tc.current_position()
    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        from xknx.devices import TravelStatus
        return self.tc.is_traveling() and \
            self.tc.travel_direction == TravelStatus.DIRECTION_UP
    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        from xknx.devices import TravelStatus
        return self.tc.is_traveling() and \
            self.tc.travel_direction == TravelStatus.DIRECTION_DOWN
    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self.tc.is_closed()
    @property
    def assumed_state(self):
        """Return True unless we have set position with confidence through send_know_position service."""
        return self._assume_uncertain_position

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        if ATTR_POSITION in kwargs:
            self._target_position = kwargs[ATTR_POSITION]
            _LOGGER.debug(self._name + ': ' + 'async_set_cover_position: %d', self._target_position)
            await self.set_position(self._target_position)
    
    async def async_close_cover(self, **kwargs):  # pylint: disable=unused-argument
        """Close cover."""
        if self.timed:
            _LOGGER.debug(self._name + ': ' + 'async_close_cover')
            self.tc.start_travel_down()
            self._target_position = 0

            self.start_auto_updater()
        await self._gateway_handler.send(
            OWNAutomationCommand.lower_shutter(self._where)
        )

    async def async_open_cover(self, **kwargs):  # pylint: disable=unused-argument
        """Open the cover."""
        if self.timed:
            """Turn the device open."""
            _LOGGER.debug(self._name + ': ' + 'async_open_cover')
            self.tc.start_travel_up()
            self._target_position = 100

            self.start_auto_updater()
        await self._gateway_handler.send(
            OWNAutomationCommand.raise_shutter(self._where)
        )

    async def async_stop_cover(self, **kwargs):  # pylint: disable=unused-argument
        """Stop the cover."""
        _LOGGER.debug(self._name + ': ' + 'async_stop_cover')
        if self.timed: self._handle_stop()
        await self._gateway_handler.send(OWNAutomationCommand.stop_shutter(self._where))

    @callback
    def auto_updater_hook(self, now):
        """Call for the autoupdater."""
        _LOGGER.debug(self._name + ': ' + 'auto_updater_hook')
        self.async_schedule_update_ha_state()
        if self.position_reached():
            _LOGGER.debug(self._name + ': ' + 'auto_updater_hook :: position_reached')
            self.stop_auto_updater()
        self.hass.async_create_task(self.auto_stop_if_necessary())

    def stop_auto_updater(self):
        """Stop the autoupdater."""
        _LOGGER.debug(self._name + ': ' + 'stop_auto_updater')
        if self._unsubscribe_auto_updater is not None:
            self._unsubscribe_auto_updater()
            self._unsubscribe_auto_updater = None

    def position_reached(self):
        """Return if cover has reached its final position."""
        return self.tc.position_reached()

    async def set_known_action(self, **kwargs):
        """We want to do a few things when we get a position"""
        action = kwargs[ATTR_ACTION]
        if action not in ["open","close","stop"]:
          raise ValueError("action must be one of open, close or cover.")
        if action == "stop":
          self._handle_stop()
          return
        if action == "open":
          self.tc.start_travel_up()
          self._target_position = 100
        if action == "close":
          self.tc.start_travel_down()
          self._target_position = 0
        self.start_auto_updater()

    def handle_event(self, message: OWNAutomationEvent):
        """Handle an event message."""
        LOGGER.info(message.human_readable_log)
        self._attr_is_opening = message.is_opening
        self._attr_is_closing = message.is_closing
        if message.is_closed is not None:
            self._attr_is_closed = message.is_closed
        if message.current_position is not None:
            self._attr_current_cover_position = message.current_position

        self.async_schedule_update_ha_state()

    async def auto_stop_if_necessary(self):
        """Do auto stop if necessary."""
        current_position = self.tc.current_position()
        if self.position_reached() and not self._processing_known_position:
            self.tc.stop()
            if (current_position > 0) and (current_position < 100):
                _LOGGER.debug(self._name + ': ' + 'auto_stop_if_necessary :: current_position between 1 and 99 :: calling stop command')
                await self._async_handle_command(SERVICE_STOP_COVER)
            else:
                if self._send_stop_at_ends:
                    _LOGGER.debug(self._name + ': ' + 'auto_stop_if_necessary :: send_stop_at_ends :: calling stop command')
                    await self._async_handle_command(SERVICE_STOP_COVER)

    async def _async_handle_command(self, command, *args):
        """We have cover.* triggered command. Reset assumed state and known_position processsing and execute"""
        self._assume_uncertain_position = True
        self._processing_known_position = False
        cmd = "UNKNOWN"
        if command == "close_cover":
            cmd = "DOWN"
            self._state = False

        elif command == "open_cover":
            cmd = "UP"
            self._state = True
        elif command == "stop_cover":
            cmd = "STOP"
            self._state = True
            
        _LOGGER.debug(self._name + ': ' + '_async_handle_command :: %s', cmd)

        # Update state of entity
        self.async_write_ha_state()