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
try:
  from gi.repository import GObject
except ImportError:
    import gobject as GObject

BLUEZ_SERVICE_NAME = "org.bluez"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
ADAPTER_IFACE = "org.bluez.Adapter1"

class BleTools(object):
    @classmethod
    def get_bus(self):
         bus = dbus.SystemBus()

         return bus
    
    @classmethod
    def get_managed_objects(cls, bus):
        remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"),
                                   DBUS_OM_IFACE)
        return remote_om.GetManagedObjects()

    @classmethod
    def find_adapter(self, bus):
        remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"),
                               DBUS_OM_IFACE)
        objects = remote_om.GetManagedObjects()

        for o, props in objects.items():
            if LE_ADVERTISING_MANAGER_IFACE in props:
                return o

        return None

    @classmethod
    def power_adapter(self):
        adapter = self.get_adapter()

        adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                "org.freedesktop.DBus.Properties")
        adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

    @classmethod
    def reset_services_and_characteristics(cls, bus):
        objects = cls.get_managed_objects(bus)
        for path, interfaces in objects.items():
            if GATT_MANAGER_IFACE in interfaces:
                try:
                    # Unregister all GATT services
                    gatt_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, path),
                                                  GATT_MANAGER_IFACE)
                    gatt_manager.UnregisterApplication(dbus.ObjectPath(path))
                    print(f"Unregistered GATT service at {path}")
                except dbus.exceptions.DBusException as e:
                    print(f"Failed to unregister GATT service at {path}: {e}")

            if LE_ADVERTISING_MANAGER_IFACE in interfaces:
                try:
                    # Stop advertising
                    adv_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, path),
                                                 LE_ADVERTISING_MANAGER_IFACE)
                    adv_manager.UnregisterAdvertisement(dbus.ObjectPath(path))
                    print(f"Unregistered advertisement at {path}")
                except dbus.exceptions.DBusException as e:
                    print(f"Failed to unregister advertisement at {path}: {e}")

    @classmethod
    def reset_adapter(cls, bus):
        adapter = cls.find_adapter(bus)
        if adapter:
            adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                           "org.freedesktop.DBus.Properties")
            # Reset adapter properties
            adapter_props.Set(ADAPTER_IFACE, "Discoverable", dbus.Boolean(0))
            adapter_props.Set(ADAPTER_IFACE, "Powered", dbus.Boolean(0))
            adapter_props.Set(ADAPTER_IFACE, "Powered", dbus.Boolean(1))
            print(f"Adapter {adapter} reset successfully.")
        else:
            print("No adapter found to reset.")

if __name__ == "__main__":
    try:
        bus = BleTools.get_bus()
        BleTools.reset_services_and_characteristics(bus)
        BleTools.reset_adapter(bus)
    except dbus.exceptions.DBusException as e:
        print(f"Error communicating with DBus: {e}")
