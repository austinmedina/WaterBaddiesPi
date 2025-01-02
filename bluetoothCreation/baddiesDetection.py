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
import time
import random

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
        super().__init__(index, self.BADDIES_SVC_UUID, True)
        self.add_characteristic(SensorCharacteristic(
            self, "Plastic", "00000002-710e-4a5b-8d75-3e5b444bc3cf", "2901", "Microplastic Concentration"))
        self.add_characteristic(SensorCharacteristic(
            self, "Metal", "00000002-810e-4a5b-8d75-3e5b444bc3cf", "2904", "Metal Concentration"))
        self.add_characteristic(SensorCharacteristic(
            self, "Inorganics", "00000002-910e-4a5b-8d75-3e5b444bc3cf", "2903", "Inorganics Concentration"))

class SensorCharacteristic(Characteristic):
    def __init__(self, service, name, uuid, descriptor_uuid, descriptor_value):
        self.notifying = False
        self.concentration = "0"  # Default value
        self.name = name
        super().__init__(uuid, ["notify", "read"], service)
        self.add_descriptor(SensorDescriptor(self, descriptor_uuid, descriptor_value))
        threading.Thread(target=self.update_sensor_data, daemon=True).start()

    def update_sensor_data(self):
        while True:
            self.concentration = str(random.randint(1, 20))
            if self.notifying:
                self.notify_concentration()
            time.sleep(5)  # Adjust as needed

    def get_concentration(self):
        return [dbus.Byte(c.encode()) for c in self.concentration]

    def notify_concentration(self):
        value = self.get_concentration()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True
        self.notify_concentration()

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        return self.get_concentration()

class SensorDescriptor(Descriptor):
    def __init__(self, characteristic, uuid, value):
        self.value = value
        super().__init__(uuid, ["read"], characteristic)

    def ReadValue(self, options):
        return [dbus.Byte(c.encode()) for c in self.value]
    INORGANICS_DESCRIPTOR_UUID = "2903"
    INORGANICS_DESCRIPTOR_VALUE = "Inorganics Concentration"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.INORGANICS_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.INORGANICS_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

if __name__ == "__main__":
    #Initialize the D-Bus main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    #Get the system bus
    bus = dbus.SystemBus()

    #Reset services and characteristics
    BleTools.reset_services_and_characteristics(bus)
    BleTools.reset_adapter(bus)

    #Create bluetooth application
    app = Application()
    app.add_service(BaddiesDetectionService(0))
    app.register()

    #Create and register advertisement for the application
    adv = BaddiesAdvertisement(0)
    adv.register()

    # Run the main loop
    loop = GLib.MainLoop()
    try:
        app.run()
        loop.run()
    except KeyboardInterrupt:
        app.quit()
        loop.quit()
