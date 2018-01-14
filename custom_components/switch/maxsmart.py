"""
Support for a MaxSmart Power Switch.

"""

import logging

import requests
import voluptuous as vol

from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, CONF_HOST)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'MaxSmart switch'

ATTR_CURRENT_CONSUMPTION = 'Current Consumption'
ATTR_CURRENT_CONSUMPTION_UNIT = 'W'

ATTR_CURRENT_AMPAGE = 'Current Amps'
ATTR_CURRENT_AMPAGE_UNIT = 'A'

CONF_PORTS = 'ports'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PORTS): cv.positive_int,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the outlets."""

    dev = []

    number_outlets = config.get(CONF_PORTS) # MaxSmart Power Strip EU
    for number in range(1, number_outlets+1):
        dev.append(SmartSwitch(
            config.get(CONF_HOST),
            config.get(CONF_NAME),
            number))

    add_devices(dev)

class SmartSwitch(SwitchDevice):
    """Representation of a single outlet"""

    def __init__(self, host, name, number):
        """Initialize the switch."""

        self._host = host
        self._name = name
        self._number = number
        self._now_power = 0.0
        self._now_amp = 0.0
        self._state = False

    @property
    def name(self):
        """Return the name of the outlet."""
        return self._name+" "+str(self._number)

    @property
    def state_attributes(self):
        """Return the state attributes of the device."""
        attrs = {}
        attrs[ATTR_CURRENT_CONSUMPTION] = "%.1f %s" % \
                (self._now_power, ATTR_CURRENT_CONSUMPTION_UNIT)
        attrs[ATTR_CURRENT_AMPAGE] = "%.1f %s" % \
                (self._now_amp, ATTR_CURRENT_AMPAGE_UNIT)
        return attrs

    @property
    def current_power_watt(self):
        """Return the current power usage in watt."""
        return self._now_power

    @property
    def is_on(self):
        """Return Switch State"""
        return self._state

    def turn_on(self):
        """Turn the switch on."""
        requests.get('http://'+self._host+'/?cmd=200&json={"port":'+str(self._number)+
                     ', "state":1}')

    def turn_off(self):
        """Turn the switch off."""
        requests.get('http://'+self._host+'/?cmd=200&json={"port":'+str(self._number)+
                     ', "state":0}')

    def update(self):
        """get state from outlet."""
        try:
            request = requests.get('http://'+self._host+'/?cmd=511').json()['data']
            _LOGGER.debug(request)
            self._state = request['switch'][self._number-1]
            self._now_power = float(request['watt'][self._number-1])
            self._now_amp = float(request['amp'][self._number-1])
        except (TypeError, ValueError):
            self._now_power = None
            _LOGGER.error('Error while reading from MaxSmart Power Outlet')
