import dbus
import dbus.mainloop.glib
from gi.repository import GLib
from time import sleep

# D-Bus main loop setup
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

# BlueZ service on D-Bus
bluez_service = bus.get("org.bluez", "/org/bluez")

# Get the Bluetooth adapter (usually 'hci0')
adapter = bluez_service.getManagedObjects()["/org/bluez/hci0"]

# Start advertising (make the Raspberry Pi discoverable)
adapter["org.freedesktop.DBus.Properties"].Set("org.bluez.Adapter1", "Powered", True)
adapter["org.freedesktop.DBus.Properties"].Set("org.bluez.Adapter1", "Discoverable", True)
adapter["org.freedesktop.DBus.Properties"].Set("org.bluez.Adapter1", "Pairable", True)
adapter["org.freedesktop.DBus.Properties"].Set("org.bluez.Adapter1", "Connectable", True)

# Define UUIDs for the GATT service and characteristic
SERVICE_UUID = "12345678-1234-1234-1234-1234567890ab"
CHARACTERISTIC_UUID = "87654321-4321-4321-4321-9876543210ab"

# Define the GATT service and characteristic
# Create a GATT service and add a characteristic that can be read
def create_service():
    service = bluez_service.createGattService(SERVICE_UUID)
    characteristic = service.createGattCharacteristic(CHARACTERISTIC_UUID, read=True)

    # Set the value that will be sent to the app (data to send)
    characteristic.value = dbus.Array([dbus.Byte(x) for x in bytearray("Hello from Pi!")])

    return service

# Start advertising the service
def start_advertising(service):
    advertising_manager = bluez_service.getObject("/org/bluez/advertising_manager0")
    advertising_manager.RegisterAdvertisement(service)

service = create_service()
start_advertising(service)

print("Advertising Bluetooth availability...")
GLib.MainLoop().run()
