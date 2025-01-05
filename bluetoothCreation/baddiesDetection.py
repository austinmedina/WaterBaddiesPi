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

from tools.advertisement import Advertisement
from tools.service import Application, Service, Characteristic, Descriptor
from tools.bletools import BleTools

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

class BaddiesAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Baddies Detection System")
        self.include_tx_power = True

class BaddiesDetectionService(Service):
    BADDIES_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        Service.__init__(self, index, self.BADDIES_SVC_UUID, True)
        self.add_characteristic(GenericCharacteristic(self, "00000002-710e-4a5b-8d75-3e5b444bc3cf", ["notify", "read"], "2901", "Microplastic Concentration"))
        self.add_characteristic(GenericCharacteristic(self, "00000002-810e-4a5b-8d75-3e5b444bc3cf", ["notify", "read"], "2904", "Metal Concentration"))
        self.add_characteristic(GenericCharacteristic(self, "00000002-910e-4a5b-8d75-3e5b444bc3cf", ["notify", "read"], "2903", "Inorganics Concentration"))

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
        
        threading.Thread(target=self.ValueThread, daemon=True).start()

    def get_concentration(self):
        concentration_value = str(random.randint(60, 150))
        
        # Convert the concentration value to a byte list
        value = [dbus.Byte(c.encode()) for c in concentration_value]

        return value

    def set_concentration_callback(self):
        if self.notifying:
            value = self.get_concentration()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_concentration()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        
        #This is used to periodically check the concentrationm(I think, at least once)
        #self.add_timeout(NOTIFY_TIMEOUT, self.set_concentration_callback)

        self.add_timeout(NOTIFY_TIMEOUT, self.StopNotify)
        
    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_concentration()

        return value
        
    def ValueThread(self):
        while True:
            # Fetch and update concentration periodically
            self.StartNotify()
            # Wait for a period before updating again (e.g., 10 seconds)
            time.sleep(10)

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
