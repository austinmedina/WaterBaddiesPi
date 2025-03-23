#!/usr/bin/python3

"""Copyright (c) 2019, Douglas Otwell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import threading
import random
import time

from .tools.advertisement import Advertisement
from .tools.service import Application, Service, Characteristic, Descriptor
from .tools.bletools import BleTools

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 10000

class BaddiesAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Baddies Detection System")
        self.include_tx_power = True

class BaddiesDetectionService(Service):
    BADDIES_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        Service.__init__(self, index, self.BADDIES_SVC_UUID, True)
        self.add_characteristic(GenericCharacteristic(self, "00000002-110e-4a5b-8d75-3e5b444bc3cf", ["notify", "read"], "2901", "Microplastic"))
        self.add_characteristic(GenericCharacteristic(self, "00000002-210e-4a5b-8d75-3e5b444bc3cf", ["notify", "read"], "2901", "Lead"))
        self.add_characteristic(GenericCharacteristic(self, "00000002-310e-4a5b-8d75-3e5b444bc3cf", ["notify", "read"], "2901", "Cadmium"))
        self.add_characteristic(GenericCharacteristic(self, "00000002-410e-4a5b-8d75-3e5b444bc3cf", ["notify", "read"], "2901", "Mercury"))
        self.add_characteristic(GenericCharacteristic(self, "00000002-510e-4a5b-8d75-3e5b444bc3cf", ["notify", "read"], "2901", "Phosphate"))
        self.add_characteristic(GenericCharacteristic(self, "00000002-610e-4a5b-8d75-3e5b444bc3cf", ["notify", "read"], "2901", "Nitrate"))
        self.add_characteristic(GenericCharacteristic(self, "00000002-710e-4a5b-8d75-3e5b444bc3cf", ["notify", "read"], "2901", "ChangeKey"))
        
class GenericCharacteristic(Characteristic):
    def __init__(self, service, UUID, options, desciptorUUID, descriptorValue, concentrationFunction = None):
        self.notifying = False
        self.uuid = UUID
        self.options = options
        self.concentrationFunction = concentrationFunction

        Characteristic.__init__(
                self, UUID,
                options, service)
        self.add_descriptor(GenericDescriptor(self, desciptorUUID, descriptorValue))
         
    def StartNotify(self):
        self.notifying = True
        value = self.ReadValue([])
        print("Value: " + str(value))

        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        print("Notified")

        self.add_timeout(NOTIFY_TIMEOUT, self.StopNotify)
        
    def StopNotify(self):
        self.notifying = False
        
    def ReadValue(self, options):
        value = [dbus.Byte(c.encode()) for c in self.value]
 
        return value    
            
    def WriteValue(self, value):
        self.value = value
        self.StartNotify()
        print("Written value and notifying")

class GenericDescriptor(Descriptor):

    def __init__(self, characteristic, UUID, value):
        self.uuid = UUID
        self.value = value
        
        Descriptor.__init__(
                self, self.uuid,
                ["read"],
                characteristic)
        

    def ReadValue(self, options):
        value = []
        desc = self.value

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value
    
if __name__ == "__main__":
    
    #Initialize the D-Bus main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    #Get the system bus
    bus = dbus.SystemBus()
    
    BleTools.power_adapter(bus)
    BleTools.setDiscoverable(bus, 1)

    #Create bluetooth application
    app = Application()
    app.add_service(BaddiesDetectionService(0))
    app.register()

    #Create and register advertisement for the application
    adv = BaddiesAdvertisement(0)
    adv.register()
    try:
        app.run()
    except KeyboardInterrupt:
        BleTools.setDiscoverable(bus, 0)
        adv.unregister()
        app.quit()
