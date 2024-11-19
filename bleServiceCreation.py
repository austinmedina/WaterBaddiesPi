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

class CharacteristicUserDescriptionDescriptor(Descriptor):
    """
    Writable CUD descriptor.
    """

    CUD_UUID = "2901"

    def __init__(
        self, bus, index, characteristic,
    ):

        self.value = array.array("B", characteristic.description)
        self.value = self.value.tolist()
        Descriptor.__init__(self, bus, index, self.CUD_UUID, ["read"], characteristic)

    def ReadValue(self, options):
        return self.value

    def WriteValue(self, value, options):
        if not self.writable:
            raise NotPermittedException()
        self.value = value
        
class PlasticConcetrationCharacteristic(Characteristic):
    uuid = "4116f8d2-9f66-4f58-a53d-fc7440e7c14e"
    descrition = b"Get the average concentration of microplastics in the water sample in parts per microliter"
    
    def __init__(self, bus, index, service):
        Characteristic.__init_(
            self, bus, index, self.uuid, ["encrypt-read"], service
        )
        
        self.value = bytearray(84, "utf8")
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus 1, self))
        
    def readValue(self):
        try:
            self.value = bytearray(84, "utf8")
        except Exception as e:
            self.value = bytearray(-1, encoding="utf8")
        
        return self.value
   
class MetalConcetrationCharacteristic(Characteristic):
    uuid = "4116f8d2-9f66-4f58-a53d-fc7440e7c14f"
    descrition = b"Get the average concentration of metals in the water sample in parts per microliter"
    
    def __init__(self, bus, index, service):
        Characteristic.__init_(
            self, bus, index, self.uuid, ["encrypt-read"], service
        )
        
        self.value = bytearray(84, "utf8")
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus 1, self))
        
    def readValue(self):
        try:
            self.value = bytearray(84, "utf8")
        except Exception as e:
            self.value = bytearray(-1, encoding="utf8")
        
        return self.value
        
class InorganicConcetrationCharacteristic(Characteristic):
    uuid = "4116f8d2-9f66-4f58-a53d-fc7440e7c14d"
    descrition = b"Get the average concentration of inorganics in the water sample in parts per microliter"
    
    def __init__(self, bus, index, service):
        Characteristic.__init_(
            self, bus, index, self.uuid, ["encrypt-read"], service
        )
        
        self.value = bytearray(84, "utf8")
        self.add_descriptor(CharacteristicUserDescriptionDescriptor(bus 1, self))
        
    def readValue(self):
        try:
            self.value = bytearray(84, "utf8")
        except Exception as e:
            self.value = bytearray(-1, encoding="utf8")
        
        return self.value
        
class BaddiesAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_manufacturer_data(0xFFFF, [0x70, 0x74],)
        
        self.add_service_uuid(BaddiesS1Service.DETECTION_SVC_UUID)
        
        self.add_local_name("BaddiesDetectionSystem")
        self.include_tx_power = True
        
class BaddiesS1Service(Service):
    """
    Dummy test service that provides characteristics and descriptors that
    exercise various API functionality.

    """

    DETECTION_SVC_UUID = "12634d89-d598-4874-8e86-7d042ee07ba7"

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.ESPRESSO_SVC_UUID, True)
        self.add_characteristic(PlasticConcetrationCharacteristic(bus, 0, self))
        self.add_characteristic(MetalConcetrationCharacteristic(bus, 1, self))
        self.add_characteristic(InorganicConcetrationCharacteristic(bus, 2, self))
    
def main():
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
    
    logger.info("Registering GATT application...")
    
    app = Application(bus)
    app.add_service(BaddiesS1Service(bus, 2))
    service_manager.RegisterApplication(
        app.get_path(),
        {},
        reply_handler=register_app_cb,
        error_handler=register_app_error_cb,
    )
    
if __name__=='__main__':
    main()
    
    
    
    
    
