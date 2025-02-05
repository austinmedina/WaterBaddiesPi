from bluetoothCreation.baddiesDetection import BaddiesAdvertisement, BaddiesDetectionService
from bluetoothCreation.tools import BleTools
from bluetoothCreation.tools.service import Application
import dbus
import dbus.mainloop.glib
import threading

class System:

    def __init__(self):
        self.bluetooth = None
        self.bus = dbus.SystemBus()
        self.app = None
        self.adv = None
        threading.Thread(target=self.listenForBluetoothRestart).start()
        threading.Thread(target=self.listenForDetectionStart).start()
        
    
    def startBluetooth(self):
        #Initialize the D-Bus main loop
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        #Get the system bus
        self.bus = dbus.SystemBus()

        BleTools.power_adapter(self.bus)
        BleTools.setDiscoverable(self.bus, 1)

        #Create bluetooth application
        self.app = Application()
        self.app.add_service(BaddiesDetectionService(0))
        self.app.register()

        #Create and register advertisement for the application
        self.adv = BaddiesAdvertisement(0)
        self.adv.register()
        try:
            self.app.run()
        except:
            print()

    def restartBluetooth(self):
        BleTools.setDiscoverable(self.bus, 0)
        self.adv.unregister()
        self.app.quit()
        self.startBluetooth()

    def start(self):
        pass

    def listenForDetectionStart(self):
        pass

    def listenForBluetoothRestart(self):
        pass

    def microplasticDetection(self):
        sum = 0
        for i in range(5):
            print("Starting microplastic slide" + i+1)
            dispenseSlide()
            moveSlideUnderDropper()
            dispenseWater()
            moveSlideUnderMicroscope()
            imagePath = captureMicroscopeImage()
            quantity = analyzeImage(imagePath)
            sum += quantity
            ejectSlide()

        concentration = sum/5    
        chars = self.app.get_characteristics()
        #get the characteristic and startNotify with the new value
        

    
    def startDetection(self):
        print("Initiating Water Baddies Detection")
        threading.Thread(target=self.microplasticDetection).start()
        threading.Thread(target=self.InorganicsMetalDetection).start()

if __name__ == "__main__":
    System()

