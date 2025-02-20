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

from breakpointSensor import IRSensor

from paperfluidic_analysis import analyzeColorimetric
from microscope_analysis import analyzeMicroplastics

class SlideNotDetectedError(Exception):
    """Exception raised when a cartridge is not detected"""

    def __init__(self, message="Cartridge not detected. Ejecting slide"):
        self.message = message
        super().__init__(self.message)

class ImageCaptureError(Exception):
    """Exception raised when an image capture runs into an error"""

    def __init__(self, message="Error while capturing image. Ejecting slide"):
        self.message = message
        super().__init__(self.message)

class ImageAnalysisError(Exception):
    """Exception raised when an image capture runs into an error"""

    def __init__(self, message="Error while capturing image. Ejecting slide"):
        self.message = message
        super().__init__(self.message)        

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

    def resetPlasticConveyorBelt(self):
        ir = IRSensor(26)
        detected = ir.is_object_detected()
        while (not detected):
            print("Calibrating microplastic conveyor belt")
            #Move the motors until the nub is detected?
            detected = ir.is_object_detected()

    def cancelMicroplastic(self):
        print("Aborting Microplastic Detection")
        #Maybe display it on the monitor
        self.resetPlasticConveyorBelt()
        return

    def verifySlideLocationDropper(self):
        ir = IRSensor(26)
        detected = ir.is_object_detected()
        if (not detected):
            raise SlideNotDetectedError("Microplastic slide did not move under dropper. Ejecting slide")
        
        return
    
    def verifySlideLocationMicroscope(self):
        ir = IRSensor(26)
        detected = ir.is_object_detected()
        if (not detected):
            raise SlideNotDetectedError("Microplastic slide did not move under microscope. Ejecting slide")
        
        return
    
    def moveUnderPlasticDropper(self):
        try:
            print("Fetching microplastic slide and moving slide under dropper")

            # Move conveyor here

            self.verifySlideLocationDropper()

            return
        except SlideNotDetectedError as se:
            print("Slide not detected after moving microplastic slide under dropper")
            raise se
        except Exception as e:
            print("Unexpected error while moving microplastic slide under dropper")
            raise e
    
    def movePlasticUnderMicroscope(self):
        try:
            print("Moving microplastic slide under microscope")

            # Move conveyor here

            self.verifySlideLocationMicroscope()

            return
        except SlideNotDetectedError as se:
            print("Slide not detected after moving microplastic slide under microscope")
            raise se
        except Exception as e:
            print("Unexpected error while moving microplastic slide under microscope")
            raise e
    
    def dispensePlasticWater(self):
        return
    
    def captureMicroscopeImage(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error opening video stream or file")
            raise Exception("Couldnt open microscope stream")
        
        ret, frame = cap.read()

        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            raise Exception("Couldnt open microscope picture frame")
        
        path = f'plasticImages/{datetime.now().strftime("%F %T.%f")[:-3]}.png'
        cv2.imwrite(path, frame)

        return path

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
        try:
            self.resetPlasticConveyorBelt()
            sum = 0
            for i in range(5):
                print("Starting microplastic slide" + str(i+1))
                self.moveUnderPlasticDropper()
                self.dispensePlasticWater()
                self.movePlasticUnderMicroscope()
                try:
                    imagePath = self.captureMicroscopeImage()
                    print(f"Microplastic image path: {imagePath}")
                except Exception as e:
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing image from the micropscope. Canceling microplastic job!")

                try:    
                    testImagePath = ""
                    quantity = analyzeMicroplastics(testImagePath)
                    #quantity = analyzeMicroplastics(imagePath)
                except Exception as e:
                    print(f"Error during image analysis: {e}")
                    raise ImageCaptureError("Error during capturing image from the micropscope. Canceling microplastic job!")
                
                sum += quantity
                self.resetPlasticConveyorBelt()

            concentration = sum/5
            
            mpChar = self.getCharacteristic("Microplastic")
            if (mpChar):
                mpChar.WriteValue(str(concentration))
                print("Updated value:"+ str(concentration))
            else:
                print("characteristic none")
        except Exception as e:
            print(f"Caught exception: {e}")
        except ImageCaptureError as ie:
            print(f"Caught image capture exception: {ie}")
        except ImageAnalysisError as ia:
            print(f"Caught image analysis exception: {ia}")
        finally:
            try:
                self.cancelMicroplastic()
            except Exception as ee:
                print(f"Fatal error while canceling microplastic detection, after an error had already occured. FATAL ERROR: {ee}")
            return

    def capturePiImage():
        picam = PiCamera2()
        picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        path = f'paperfluidicImages/{datetime.now().strftime("%F %T.%f")[:-3]}.png'
        picam.start_and_capture(path)
        return path

    def resetPaperConveyorBelt(self):
        ir = IRSensor(26)
        detected = ir.is_object_detected()
        while (not detected):
            print("Calibrating microplastic conveyor belt")
            #Move the motors until the nub is detected?
            detected = ir.is_object_detected()

    def cancelPaper(self):
        print("Aborting Paper Detection")
        self.resetPaperConveyorBelt()
        return

    def verifyPaperLocationDropper(self):
        ir = IRSensor(26)
        detected = ir.is_object_detected()
        if (not detected):
            raise SlideNotDetectedError("Paperfluidics did not move under dropper. Ejecting slide")
        
        return
    
    def verifyPaperLocationMicroscope(self):
        ir = IRSensor(26)
        detected = ir.is_object_detected()
        if (not detected):
            raise SlideNotDetectedError("Paperfluidics did not move under microscope. Ejecting slide")
        
        return
    
    def moveUnderWaterDropper(self):
        try:
            print("Moving paperfluidics under microscope")

            # Move conveyor here

            self.verifyPaperLocationDropper()

            return
        except SlideNotDetectedError as se:
            print("Slide not detected after moving paperfluidics slide under dropper")
            raise se
        except Exception as e:
            print("Unexpected error while moving paperfluidics slide under dropper")
            raise e
    
    def moveUnderCamera(self):
        try:
            print("Moving paperfluidics slide under PiCamera")

            # Move conveyor here

            self.verifyPaperLocationMicroscope()

            return
        except SlideNotDetectedError as se:
            print("Slide not detected after moving paperfluidics slide under PiCamera")
            raise se
        except Exception as e:
            print("Unexpected error while moving paperfluidics slide under PiCamera")
            raise e
        
    def dispenseFluidicWater(self):
        pass
                
    def InorganicsMetalDetection(self):
        try:
            self.resetPaperConveyorBelt()
            self.moveUnderWaterDropper()
            self.dispenseFluidicWater()
            self.moveUnderCamera()
            try:
                imagePath = self.capturePiImage()
                print(f"First paperfluidics image: {imagePath}")
                time.sleep(30)
                leadImagePath = self.capturePiImage() #Just capture lead image
                print(f"Lead paperfluidics image: {leadImagePath}")

                #Just for testing
                testImagePath = ""
                testLeadImagePath = ""
            except Exception as e:
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing image from the PiCamera. Canceling paperfluidics job!")
            
            try:
                #leadConcentration = analyzeColorimetric(imagePath, leadImagePath)['lead']
                leadConcentration = analyzeColorimetric(testImagePath, testLeadImagePath)['lead']
            except Exception as e:
                    print(f"Error during image analysis: {e}")
                    raise ImageCaptureError("Error during capturing image from the PiCamera. Canceling paperfluidics job!")
            
            time.sleep(530)

            try:
                finalImagePath = self.capturePiImage()
                print(f"Final paperfluidics image: {finalImagePath}")
                
                testFinalImagePath = ""
            except Exception as e:
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing image from the PiCamera. Canceling paperfluidics job!")
            
            try:
                #concentration = analyzeColorimetric(imagePath, finalImagePath)
                concentration = analyzeColorimetric(testImagePath, testFinalImagePath)
                concentration['Lead'] = leadConcentration
            except Exception as e:
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing image from the PiCamera. Canceling paperfluidics job!")

            leadChar = self.getCharacteristic("Lead")
            if (leadChar):
                leadChar.WriteValue(str(concentration["Lead"]))
                print("Updated value:"+ str(concentration["Lead"]))
            else:
                print("Lead characteristic not found")

            arsenicChar = self.getCharacteristic("Mercury")
            if (arsenicChar):
                arsenicChar.WriteValue(str(concentration["Mercury"]))
                print("Updated value:"+ str(concentration["Mercury"]))
            else:
                print("Mercury characteristic not found")

            cadmiumChar = self.getCharacteristic("Cadmium")
            if (cadmiumChar):
                cadmiumChar.WriteValue(str(concentration["Cadmium"]))
                print("Updated value:"+ str(concentration["Cadmium"]))
            else:
                print("Cadmium characteristic not found")

            nitrateChar = self.getCharacteristic("Nitrate")
            if (nitrateChar):
                nitrateChar.WriteValue(str(concentration["Nitrate"]))
                print("Updated value:"+ str(concentration["Nitrate"]))
            else:
                print("Nitrate characteristic not found")

            nitriteChar = self.getCharacteristic("Nitrite")
            if (nitriteChar):
                nitriteChar.WriteValue(str(concentration["Nitrite"]))
                print("Updated value:"+ str(concentration["Nitrite"]))
            else:
                print("Nitrite characteristic not found")
        except Exception as e:
            print(f"Caught exception: {e}")
        except ImageCaptureError as ie:
            print(f"Caught image capture exception: {ie}")
        except ImageAnalysisError as ia:
            print(f"Caught image analysis exception: {ia}")
        finally:
            try:
                self.cancelPaper()
            except Exception as ee:
                print(f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        
    def ArsenicDetection(self):
        try:
            print("Do some arsenic testing")
            return
        except Exception as e:
            print(f"Caught exception: {e}")
        except ImageCaptureError as ie:
            print(f"Caught image capture exception: {ie}")
        except ImageAnalysisError as ia:
            print(f"Caught image analysis exception: {ia}")
        finally:
            try:
                self.cancelPaper()
            except Exception as ee:
                print(f"Fatal error while canceling arsenic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
    
    def startDetection(self):
        print("Initiating Water Baddies Detection")
        time.sleep(10)
        microplasticDetectionThread = threading.Thread(target=self.microplasticDetection)
        microplasticDetectionThread.start()

        inorganicMetalThread = threading.Thread(target=self.InorganicsMetalDetection)
        inorganicMetalThread.start()

        arsenicDetectionThread = threading.Thread(target=self.ArsenicDetection)
        arsenicDetectionThread.start()

        microplasticDetectionThread.join()
        inorganicMetalThread.join()
        arsenicDetectionThread.join()

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
        
    

