"""Constants for the MyHome component."""
import logging

LOGGER = logging.getLogger(__package__)
DOMAIN = "myhome_timed"

ATTR_MESSAGE = "message"

CONF = "config"
CONF_ENTITIES = "entities"
CONF_ADDRESS = "address"
CONF_OWN_PASSWORD = "password"
CONF_FIRMWARE = "firmware"
CONF_SSDP_LOCATION = "ssdp_location"
CONF_SSDP_ST = "ssdp_st"
CONF_DEVICE_TYPE = "deviceType"
CONF_DEVICE_MODEL = "model"
CONF_MANUFACTURER = "manufacturer"
CONF_MANUFACTURER_URL = "manufacturerURL"
CONF_UDN = "UDN"
CONF_WORKER_COUNT = "command_worker_count"
CONF_PARENT_ID = "parent_id"
CONF_WHO = "who"
CONF_WHERE = "where"
CONF_ZONE = "zone"
CONF_DIMMABLE = "dimmable"
CONF_GATEWAY = "gateway"
CONF_DEVICE_CLASS = "class"
CONF_INVERTED = "inverted"
CONF_ADVANCED_SHUTTER = "advanced"
CONF_HEATING_SUPPORT = "heat"
CONF_COOLING_SUPPORT = "cool"
CONF_FAN_SUPPORT = "fan"
CONF_STANDALONE = "standalone"
CONF_CENTRAL = "central"
CONF_SHORT_PRESS = "pushbutton_short_press"
CONF_SHORT_RELEASE = "pushbutton_short_release"
CONF_LONG_PRESS = "pushbutton_long_press"
CONF_LONG_RELEASE = "pushbutton_long_release"

CONF_TIMED = 'timed'
DEFAULT_TIMED = False
DEFAULT_ADVANCED = False
CONF_TRAVELLING_TIME_DOWN = 'travelling_time_down'
CONF_TRAVELLING_TIME_UP = 'travelling_time_up'
CONF_SEND_STOP_AT_ENDS = 'send_stop_at_ends'

ATTR_ACTION = 'action'
ATTR_POSITION_TYPE = 'position_type'
ATTR_POSITION_TYPE_CURRENT = 'current'
ATTR_POSITION_TYPE_TARGET = 'target'
ATTR_UNCONFIRMED_STATE = 'unconfirmed_state'
SERVICE_SET_KNOWN_POSITION = 'set_known_position'
SERVICE_SET_KNOWN_ACTION = 'set_known_action'
DEFAULT_TRAVEL_TIME = 25
DEFAULT_SEND_STOP_AT_ENDS = False
DEFAULT_ADVANCED = False