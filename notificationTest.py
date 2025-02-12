import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import dbus.service

# Adapt these values to your needs
SERVICE_UUID = "12345678-1234-1234-1234-123456789012"  # Replace with your service UUID
CHARACTERISTIC_UUID = "abcdef01-1234-1234-1234-123456789012" # Replace with your characteristic UUID
ADAPTER_NAME = "hci0"  # Replace if necessary

class NotificationService(dbus.service.Object):
    def __init__(self, bus, object_path):
        dbus.service.Object.__init__(self, bus, object_path)
        self.notifying = False

    @dbus.service.method("org.bluez.GattService1", in_signature="", out_signature="a{sv}")
    def GetProperties(self):
        return {
            "UUID": SERVICE_UUID,
            "Primary": True,
            "Characteristics": [
                dbus.ObjectPath(self.characteristic.get_path())
            ],
        }

    @dbus.service.method("org.bluez.GattService1", in_signature="", out_signature="")
    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True
        print("Notifications started")
        self.send_notification() # Send the initial notification

    @dbus.service.method("org.bluez.GattService1", in_signature="", out_signature="")
    def StopNotify(self):
        if not self.notifying:
            return
        self.notifying = False
        print("Notifications stopped")

    def send_notification(self):
        if not self.notifying:
            return

        value = [0x01, 0x02, 0x03] # Example notification data (bytes)
        self.characteristic.set_value(value)  # Update the characteristic value

        try:
            self.characteristic.PropertiesChanged(
                "org.bluez.GattCharacteristic1",
                {"Value": value},
                []
            )
            print(f"Notification sent: {value}")
        except dbus.exceptions.DBusException as e:
            print(f"Error sending notification: {e}")

        # You can use a timer to send notifications periodically
        # GLib.timeout_add_seconds(5, self.send_notification)  # Example: every 5 seconds



class NotificationCharacteristic(dbus.service.Object):
    def __init__(self, bus, object_path, service):
        dbus.service.Object.__init__(self, bus, object_path)
        self.service = service
        self.value = []

    def set_value(self, value):
        self.value = value

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="", out_signature="a{sv}")
    def GetProperties(self):
        return {
            "UUID": CHARACTERISTIC_UUID,
            "Service": self.service.get_path(),
            "Value": self.value,
            "Notifiable": True,
        }

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="", out_signature="ay")
    def ReadValue(self):  # Implement if needed
        print("ReadValue called")
        return self.value

    @dbus.service.method("org.bluez.GattCharacteristic1", in_signature="ay", out_signature="")
    def WriteValue(self, value): # Implement if needed
        print(f"WriteValue called: {value}")
        self.value = value



if __name__ == "__main__":
    dbus.mainloop.glib.DBusGMainLoop()
    bus = dbus.SystemBus(mainloop=dbus.mainloop.glib.DBusGMainLoop())

    # *** CORRECT WAY TO CLAIM THE BLUEZ NAME (AND FIX PERMISSIONS) ***
    try:
        reply = bus.request_name("org.bluez") # Correct! No flags.
        if reply == 1:  # 1 means primary owner
            print("Successfully claimed the 'org.bluez' name.")
        elif reply == 2:  # 2 means already owned by this process.
            print("'org.bluez' name is already owned by this process.")
        else:
            print("Failed to claim the 'org.bluez' name.  Check permissions.")
            exit(1) # Exit if we can't get the name

    except dbus.exceptions.DBusException as e:
        print(f"Error claiming 'org.bluez' name: {e}")
        print("Ensure that your user has the necessary permissions to access BlueZ via D-Bus.")
        exit(1)

    # ... (Get adapter, start advertising - you'll need to implement this)

    # *** CORRECT WAY TO REGISTER OBJECTS (FINALLY!) ***
    bus.register_object(service_path, service)         # Use the bus!
    bus.register_object(characteristic_path, characteristic)  # Use the bus!

    print("GATT service and characteristic registered.")

    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Exiting...")
        # Unregister objects before exiting if needed (Important!)
        bus.unregister_object(service_path)
        bus.unregister_object(characteristic_path)
