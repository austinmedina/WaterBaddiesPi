#!/usr/bin/env python3

import logging

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

from ble import (
    Advertisement,
    Characteristic,
    Service,
    Application,
    find_adapter,
    Descriptor,
    Agent,
)

import struct
import requests
import array
from enum import Enum

import sys

MainLoop = None
try:
    from gi.repository import GLib

    MainLoop = GLib.MainLoop
except ImportError:
    import gobject as GObject

    MainLoop = GObject.MainLoop

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)


BaddiesBaseUrl = "XXXXXXXXXXXX"

mainloop = None

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"

class BaddiesS1Service(Service):
    """
    Dummy test service that provides characteristics and descriptors that
    exercise various API functionality.

    """

    ESPRESSO_SVC_UUID = "12634d89-d598-4874-8e86-7d042ee07ba7"

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.ESPRESSO_SVC_UUID, True)
        self.add_characteristic(PowerControlCharacteristic(bus, 0, self))
        self.add_characteristic(BoilerControlCharacteristic(bus, 1, self))
        self.add_characteristic(AutoOffCharacteristic(bus, 2, self))


class BaddiesAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_manufacturer_data(0xFFFF, [0x70, 0x74],)
        
        self.add_service_uuid(BaddiesS1Service.ESPRESSO_SVC_UUID)
        
        self.add_local_name("BaddiesDetectionSystem")
        self.include_tx_power = True
    
if __name__=='__main__':
    global mainloop
    
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    ## get the system bus
    bus = dbus.SystemBus()
    # get the ble controller
    adapter = find_adapter(bus)

    if not adapter:
        logger.critical("GattManager1 interface not found")
        return

    adapter_obj = bus.get_object(BLUEZ_SERVICE_NAME, adapter)
    
    adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")

    # powered property on the controller to on
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

    # Get manager objs
    service_manager = dbus.Interface(adapter_obj, GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(adapter_obj, LE_ADVERTISING_MANAGER_IFACE)
    
    advertisment = BaddiesAdvertisement(bus, 0)
    
    ad_manager.RegisterAdvertisement(
        advertisment.get_path(),
        {},
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb,
    )
