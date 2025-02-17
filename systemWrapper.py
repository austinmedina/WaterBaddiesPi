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
import cv2

from picamera2 import PiCamera2
from libcamera import controls

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

    def verifySlideLocationDropper(self):
        return
    
    def verifySlideLocationMicroscope(self):
        return
    
    def cancelMicroplastic(self):
        print("Aborting Microplastic Detection")
        return
    
    def moveUnderPlasticDropper(self):
        try:
            print("Fetching microplastic slide and moving slide under dropper")

            self.verifySlideLocationDropper()
        except:
            print("Microplastic slide did not move to the correct position. Ejecting slide")
            self.cancelMicroplastic()
        
        return
    
    def dispensePlasticWater(self):
        return
    
    def moveSlideUnderMicroscope(self):
        try:
            print("Moving microplastic slide under microscope")

            self.verifySlideLocationMicroscope()
        except:
            print("Microplastic slide did not move to the correct position. Ejecting slide")
            self.cancelMicroplastic()
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
            self.moveUnderPlasticDropper()
            self.dispensePlasticWater()
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

    def capturePiImage():
        picam = PiCamera2()
        picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        path = f'plasticImages/{datetime.now().strftime("%F %T.%f")[:-3]}.png'
        picam.start_and_capture(path)
        pass

    def analyzeColorimetric(self, imagePath, afterImagePath):
        return {'Lead': 93, 'Cadmium': 96, 'Arsenic': 102, 'Nitrate': 106, 'Nitrite': 116}

    def dispensePaper(self):
        pass

    def cancelPaper(self):
        print("Aborting Paper Detection")
        return

    def verifyPaperLocationDropper(self):
        return
    
    def verifyPaperLocationMicroscope(self):
        return
    
    def moveUnderWaterDropper(self):
        try:
            print("Moving paperfluidic under dropper")

            self.verifyPaperLocationDropper()
        except:
            print("Paperfluidic did not move to the correct position. Ejecting!")
            self.cancelPaper()
        return
    
    def dispenseFluidicWater(self):
        pass
    
    def moveUnderCamera(self):
        try:
            print("Moving paperfluidic slide under camera")

            self.verifyPaperLocationMicroscope()
        except:
            print("Paperfluidic did not move to the correct position. Ejecting!")
            self.cancelPaper()
        return
                
    def InorganicsMetalDetection(self):
        self.moveUnderWaterDropper()
        self.dispenseFluidicWater()
        self.moveUnderCamera()
        imagePath = self.capturePiImage()
        time.sleep(30)
        leadImagePath = self.capturePiImage() #Just capture lead image
        leadConcentration = self.analyzeColorimetric(imagePath, leadImagePath)
        time.sleep(550)
        finalImagePath = self.capturePiImage()
        concentration = self.analyzeColorimetric(imagePath, finalImagePath)

        leadChar = self.getCharacteristic("Lead")
        if (leadChar):
            leadChar.WriteValue(str(concentration["Lead"]))
            print("Updated value:"+ str(concentration["Lead"]))
        else:
            print("Characteristic not found")

        arsenicChar = self.getCharacteristic("Arsenic")
        if (arsenicChar):
            arsenicChar.WriteValue(str(concentration["Arsenic"]))
            print("Updated value:"+ str(concentration["Arsenic"]))
        else:
            print("Characteristic not found")

        cadmiumChar = self.getCharacteristic("Cadmium")
        if (cadmiumChar):
            cadmiumChar.WriteValue(str(concentration["Cadmium"]))
            print("Updated value:"+ str(concentration["Cadmium"]))
        else:
            print("Characteristic not found")

        nitrateChar = self.getCharacteristic("Nitrate")
        if (nitrateChar):
            nitrateChar.WriteValue(str(concentration["Nitrate"]))
            print("Updated value:"+ str(concentration["Nitrate"]))
        else:
            print("Characteristic not found")

        nitriteChar = self.getCharacteristic("Nitrite")
        if (nitriteChar):
            nitriteChar.WriteValue(str(concentration["Nitrite"]))
            print("Updated value:"+ str(concentration["Nitrite"]))
        else:
            print("Characteristic not found")
    
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
        
    

