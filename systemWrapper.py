from bluetoothCreation.baddiesDetection import BaddiesAdvertisement, BaddiesDetectionService
from bluetoothCreation.tools.bletools import BleTools
from bluetoothCreation.tools.service import Application, GATT_DESC_IFACE
import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import threading
from datetime import datetime
import time
import random

class System:

    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        
        self.bluetooth = None
        self.bus = dbus.SystemBus()
        self.app = None
        self.adv = None
        self.loop = None
        self.startBluetooth()
        self.bluetoothRestartThread = threading.Thread(target=self.listenForBluetoothRestart).start()
        self.detectionStartThread = threading.Thread(target=self.listenForDetectionStart).start()
        
    
    def startBluetooth(self):

        BleTools.power_adapter(self.bus)
        BleTools.setDiscoverable(self.bus, 1)

        #Create bluetooth application
        self.app = Application()
        self.app.add_service(BaddiesDetectionService(0))
        self.app.register()

        #Create and register advertisement for the application
        self.adv = BaddiesAdvertisement(0)
        self.adv.register()
        loop_thread = threading.Thread(target=self.run_event_loop)
        loop_thread.start()

    def run_event_loop(self):
        try:
            self.loop = GLib.MainLoop()
            self.loop.run()
        except Exception as e:
            print(f"Error in DBus main loop: {e}")

    def restartBluetooth(self):
        BleTools.setDiscoverable(self.bus, 0)
        self.adv.unregister()
        self.app.quit()
        self.startBluetooth()

    def start(self):
        pass

    def listenForDetectionStart(self):
        self.startDetection()

    def listenForBluetoothRestart(self):
        pass
    
    def dispenseSlide(self):
        return
    
    def moveSlideUnderDropper(self):
        return
    
    def dispenseWater(self):
        return
    
    def moveSlideUnderMicroscope(self):
        return
    
    def captureMicroscopeImage(self):
        return "microimage-" + datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    
    def analyzeImage(self, imagePath):
        return random.randint(90,110)
    
    def ejectSlide(self):
        return
    
    def getCharacteristic(self, charName):
        chars = self.app.getServices()[0].get_characteristics()
        for characteristic in chars:
            descriptors = characteristic.get_descriptors()
            for desc in descriptors:
                bites = desc.ReadValue([])
                byteString = ''.join([chr(byte) for byte in bites])
                if (byteString == charName):
                    return characteristic
                
        return None

    def microplasticDetection(self):
        sum = 0
        for i in range(5):
            print("Starting microplastic slide" + str(i+1))
            self.dispenseSlide()
            self.moveSlideUnderDropper()
            self.dispenseWater()
            self.moveSlideUnderMicroscope()
            imagePath = self.captureMicroscopeImage()
            quantity = self.analyzeImage(imagePath)
            sum += quantity
            self.ejectSlide()

        concentration = sum/5
        
        mpChar = self.getCharacteristic("Microplastic")
        if (mpChar):
            mpChar.WriteValue(str(concentration))
            print("Updated value:"+ str(concentration))
        else:
            print("characteristic none")
        
                
    def InorganicsMetalDetection():
        mpChar = self.getCharacteristic("Lead")
        if (mpChar):
            mpChar.WriteValue(str(concentration))
            print("Updated value:"+ str(concentration))
        else:
            print("characteristic none")
    
    def startDetection(self):
        print("Initiating Water Baddies Detection")
        time.sleep(10)
        microplasticDetectionThread = threading.Thread(target=self.microplasticDetection)
        microplasticDetectionThread.start()
        inorganicMetalThread = threading.Thread(target=self.InorganicsMetalDetection)
        inorganicMetalThread.start()
        microplasticDetectionThread.join()
        inorganicMetalThread.join()
        print("Finished detection")

if __name__ == "__main__":
    wb = System()
    try:
        while True:
            print("Still Running...")
            time.sleep(10)
    except KeyboardInterrupt:
        BleTools.setDiscoverable(wb.bus, 0)
        wb.adv.unregister()
        wb.app.quit()
        
    

