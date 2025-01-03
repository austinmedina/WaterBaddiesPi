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
        self.add_characteristic(PlasticCharacteristic(self))
        self.add_characteristic(MetalCharacteristic(self))
        self.add_characteristic(InorganicsCharacteristic(self))

class PlasticCharacteristic(Characteristic):
    PLASTIC_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.PLASTIC_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(PlasticDescriptor(self))

    def get_concentration(self):
        value = []

        strtemp = "95"
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_plastic_callback(self):
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
        self.add_timeout(NOTIFY_TIMEOUT, self.set_plastic_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_concentration()

        return value

class PlasticDescriptor(Descriptor):
    PLASTIC_DESCRIPTOR_UUID = "2901"
    PLASTIC_DESCRIPTOR_VALUE = "Microplastic Concentration"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.PLASTIC_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.PLASTIC_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value
    
class MetalCharacteristic(Characteristic):
    METAL_CHARACTERISTIC_UUID = "00000002-810e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.METAL_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(MetalDescriptor(self))

    def get_concentration(self):
        value = []

        strtemp = "100"
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_metal_callback(self):
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
        self.add_timeout(NOTIFY_TIMEOUT, self.set_metal_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_concentration()

        return value

class MetalDescriptor(Descriptor):
    METAL_DESCRIPTOR_UUID = "2904"
    METAL_DESCRIPTOR_VALUE = "Metal Concentration"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.METAL_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.METAL_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value
    
class InorganicsCharacteristic(Characteristic):
    INORGANICS_CHARACTERISTIC_UUID = "00000002-910e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.INORGANICS_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(InorganicsDescriptor(self))

    def get_concentration(self):
        value = []

        strtemp = "105"
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_inorganics_callback(self):
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
        self.add_timeout(NOTIFY_TIMEOUT, self.set_inorganics_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_concentration()

        return value

class InorganicsDescriptor(Descriptor):
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
    
    BleTools.power_adapter(bus)
    BleTools.setDiscoverable(bus)

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
        adv.unregister()
        app.quit()
