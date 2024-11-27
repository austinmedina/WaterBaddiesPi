from bluepy.btle import Peripheral, UUID, Characteristic, BTLEException
from bluepy import btle
import time

# Define the service and characteristic UUIDs
SERVICE_UUID = UUID(0x1100)
CHARACTERISTIC_UUID = UUID(0x1110)

# Create a custom peripheral class
class MyPeripheral(btle.Peripheral):
    def __init__(self):
        # We will not call 'super().__init__()' as it's not needed for a peripheral advertising service
        pass

    def startAdvertising(self):
        try:
            # Enable advertising (this is bluepy's way of advertising)
            self.advertisement = btle.Advertisement()
            self.advertisement.addServiceUUID(SERVICE_UUID)

            # Start advertising with a custom service UUID
            self.advertisement.start()
            print("Advertising started...")

            # Wait for some time for the advertisement to be visible
            while True:
                time.sleep(1)
        except BTLEException as e:
            print(f"Advertising failed: {e}")

    def addService(self):
        # Create a new service and add the characteristic
        self.service = btle.Service(SERVICE_UUID)
        self.characteristic = self.service.addCharacteristic(
            CHARACTERISTIC_UUID,
            Characteristic.PERM_READ | Characteristic.PERM_NOTIFY
        )
        self.characteristic.setValue("62 61 64 64 69 65 73")  # Sample value: 'baddies'
        print(f"Service {SERVICE_UUID} with characteristic {CHARACTERISTIC_UUID} added.")

# Create the peripheral object
peripheral = MyPeripheral()

# Add service and characteristic
peripheral.addService()

# Start the advertising
peripheral.startAdvertising()

# Keep the advertising running
while True:
    time.sleep(1)
