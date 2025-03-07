from bluetoothCreation.baddiesDetection import BaddiesAdvertisement, BaddiesDetectionService
from bluetoothCreation.tools.bletools import BleTools
from bluetoothCreation.tools.service import Application, GATT_DESC_IFACE
import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import threading
from datetime import datetime
import time

from picamera2 import Picamera2
from libcamera import controls

from breakpointSensor import IRSensor
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

import paperfluidic_analysis as pfa
from microscope_analysis import microplastic_concentration

from DisplayHAT import DisplayHat

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

class ConveyorGoAroundError(Exception):
    """Exception raised when the conveyor misses a breakpoint and goes back to the start without performing the test"""

    def __init__(self, message="Conveyor rotated all the way around to start. Aborting test. Ejecting slide"):
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
        self.kit = MotorKit()
        self.cm_step = 31
        self.startBluetooth()
        self.display = DisplayHat(self.startMicroplasticDetection, self.startInorganicsMetalDetection, self.startArsenicDetection, self.startDetection, self.restartBluetooth)
        
    
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

#     def listenForDetectionStart(self):
#         while True:
#             command = input("Enter command (BR, MP, PF): ").upper()
#             if command in ('MP'):
#                 self.startDetection()
#             elif command in ('PF'):
#                 self.startDetection()
#             else:
#                 print("Invalid command")
    
    def run_stepper(self, stepper_motor, steps, direction=stepper.FORWARD, style=stepper.SINGLE):
        for i in range(steps):
            stepper_motor.onestep(direction=direction, style=style)
            time.sleep(0.01)

    def resetConveyorBelt(self, ir, message, motor):
        print(message)
        detected = ir.is_object_detected()
        while (not detected):
#             print("Moving Conveyor Belt")
            self.run_stepper(motor, self.cm_step)
            detected = ir.is_object_detected()

    def moveConveyorToSensor(self, targetIR, startIR, message, motor):
        print(message)
        detected = targetIR.is_object_detected()
        while ((not detected)):
#             print("Moving Conveyor Belt")
            self.run_stepper(motor, self.cm_step)
            detected = targetIR.is_object_detected()
            startDetected = startIR.is_object_detected()
            if (startDetected):
                raise ConveyorGoAroundError("Conveyor belt at the start, although its not supposed to be.")
    
    def dispensePlasticWater(self):
        print("Dispensing water")
        #self.run_stepper(self.kit.stepper1, (self.cm_step * 8))
        return
    
    def captureMicroscopeImage(self):
        cap = cv2.VideoCapture(8)
        if not cap.isOpened():
            print("Error opening video stream or file")
            raise Exception("Couldnt open microscope stream")
        
        ret, frame = cap.read()

        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            raise Exception("Couldnt open microscope picture frame")
        
        path = f'plasticImages/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]}.png'
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
    
    def updateKey(self, key):
        keyChar = self.getCharacteristic("ChangeKey")
        if (keyChar):
            keyChar.WriteValue(key)
            print("Updated Key")
        else:
            print("ChangeKey characteristic none")

    def microplasticDetection(self, key):
        try:
            firstIR = IRSensor(26)
            dropperIR = IRSensor(20)
            microscopeIR = IRSensor(12)
            self.resetConveyorBelt(firstIR, "Resetting microplastic conveyor belt", self.kit.stepper1)
            time.sleep(2)
            sum = 0
            for i in range(1):
                print("Starting microplastic slide" + str(i+1))
                self.moveConveyorToSensor(dropperIR, firstIR, "Fetching microplastic slide and moving slide under dropper", self.kit.stepper1)
                time.sleep(2)
                self.dispensePlasticWater()
                time.sleep(2)
                self.moveConveyorToSensor(microscopeIR, firstIR, "Moving microplastic slide under microscope", self.kit.stepper1)
                time.sleep(2)
                try:
                    imagePath = self.captureMicroscopeImage()
                    print(f"Microplastic image path: {imagePath}")
                except Exception as e:
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing image from the micropscope. Canceling microplastic job!")

                try:    
                    testImagePath = "./test_images/Snap_027.jpg"
                    quantity = microplastic_concentration(testImagePath)
                    #quantity = microplastic_concentration(imagePath)
                except Exception as e:
                    print(f"Error during image analysis: {e}")
                    raise ImageCaptureError("Error during capturing image from the micropscope. Canceling microplastic job!")
                
                sum += quantity
                self.resetConveyorBelt(firstIR, "Resetting conveyor belt", self.kit.stepper1)

            concentration = sum
            
            mpChar = self.getCharacteristic("Microplastic")
            if (mpChar):
                mpChar.WriteValue(str(concentration))
                print("Updated value:"+ str(concentration))
                
                self.updateKey(key)
            else:
                print("Microplastic characteristic not found")
        except Exception as e:
            print(f"Caught exception: {e}")
            try:
                self.resetConveyorBelt(firstIR, "Cancelling microplastic detection and discarding any active trays", self.kit.stepper1)
            except Exception as ee:
                print(f"Fatal error while canceling microplastic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        except ImageCaptureError as ie:
            print(f"Caught image capture exception: {ie}")
            try:
                self.resetConveyorBelt(firstIR, "Cancelling microplastic detection and discarding any active trays", self.kit.stepper1)
            except Exception as ee:
                print(f"Fatal error while canceling microplastic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        except ImageAnalysisError as ia:
            print(f"Caught image analysis exception: {ia}")
            try:
                self.resetConveyorBelt(firstIR, "Cancelling microplastic detection and discarding any active trays", self.kit.stepper1)
            except Exception as ee:
                print(f"Fatal error while canceling microplastic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        

    def capturePiImage(self):
        picam = Picamera2()
        picam.configure(picam.create_still_configuration()) # Add this line
        picam.start()
        picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        path = f'paperFluidicImages/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]}.png'
        picam.capture_file(path)
        picam.close()
        return path
        
    def dispenseFluidicWater(self):
        pass
                
    def InorganicsMetalDetection(self, key):
        try:
            firstIR = IRSensor(26)
            dropperIR = IRSensor(20)
            microscopeIR = IRSensor(12)
            self.resetConveyorBelt(firstIR, "Resetting paperfluidic conveyor belt", self.kit.stepper1)
            time.sleep(2)

            self.moveConveyorToSensor(dropperIR, firstIR, "Fetching paperfluidics and moving the slide under the water dropper", self.kit.stepper1)
            time.sleep(2)
            self.dispenseFluidicWater()
            time.sleep(2)
            self.moveConveyorToSensor(microscopeIR, firstIR, "Moving paperluidics under the microscope", self.kit.stepper1)
            try:
                imagePath = self.capturePiImage()
                print(f"First paperfluidics image: {imagePath}")
                print("Waiting for lead reaction")
                time.sleep(3)
                leadImagePath = self.capturePiImage() #Just capture lead image
                print(f"Lead paperfluidics image: {leadImagePath}")

                #Just for testing
                testImagePath = "./test_images/paperfluidic.jpg"
                testLeadImagePath = "./test_images/paperfluidic_test.jpg"
            except Exception as e:
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing image from the PiCamera for lead or base image. Canceling paperfluidics job!")
            
            try:
                #leadConcentration = paperfluidic_concentration(imagePath, leadImagePath)['lead']
                print("Starting Lead Concentration Analysis")
                vals = pfa.paperfluidic_concentration(testImagePath, testLeadImagePath)
                leadConcentration = vals['Lead']
            except Exception as e:
                    print(f"Error during image analysis: {e}")
                    raise ImageCaptureError("Error analyzing lead image. Canceling paperfluidics job!")
            
            print("Waiting for paperfluidic reactions")
            time.sleep(5)

            try:
                finalImagePath = self.capturePiImage()
                print(f"Final paperfluidics image: {finalImagePath}")
                
                testFinalImagePath = "./test_images/paperfluidic_test.jpg"
            except Exception as e:
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing final image from the PiCamera. Canceling paperfluidics job!")
            
            try:
                #concentration = paperfluidic_concentration(imagePath, finalImagePath)
                concentration = pfa.paperfluidic_concentration(testImagePath, testFinalImagePath)
                concentration['Lead'] = leadConcentration
            except Exception as e:
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing image from the PiCamera. Canceling paperfluidics job!")

            leadChar = self.getCharacteristic("Lead")
            if (leadChar):
                leadChar.WriteValue(str(concentration["Lead"]))
                print("Updated value:"+ str(concentration["Lead"]))
                
                self.updateKey(key)
            else:
                print("Lead characteristic not found")

            arsenicChar = self.getCharacteristic("Mercury")
            if (arsenicChar):
                arsenicChar.WriteValue(str(concentration["Mercury"]))
                print("Updated value:"+ str(concentration["Mercury"]))
                
                self.updateKey(key)
            else:
                print("Mercury characteristic not found")

            cadmiumChar = self.getCharacteristic("Cadmium")
            if (cadmiumChar):
                cadmiumChar.WriteValue(str(concentration["Cadmium"]))
                print("Updated value:"+ str(concentration["Cadmium"]))
                
                self.updateKey(key)
            else:
                print("Cadmium characteristic not found")

            nitrateChar = self.getCharacteristic("Nitrate")
            if (nitrateChar):
                nitrateChar.WriteValue(str(concentration["Nitrate"]))
                print("Updated value:"+ str(concentration["Nitrate"]))
                
                self.updateKey(key)
            else:
                print("Nitrate characteristic not found")

            nitriteChar = self.getCharacteristic("Nitrite")
            if (nitriteChar):
                nitriteChar.WriteValue(str(concentration["Nitrite"]))
                print("Updated value:"+ str(concentration["Nitrite"]))
                
                self.updateKey(key)
            else:
                print("Nitrite characteristic not found")

            self.resetConveyorBelt(firstIR, "Resetting the paperfludics conveyor belt", self.kit.stepper1)
        except Exception as e:
            print(f"Caught exception: {e}")
            try:
                self.resetConveyorBelt(firstIR, "Canceling paperfluidics and resetting conveyor belt", self.kit.stepper1)
            except Exception as ee:
                print(f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        except ImageCaptureError as ie:
            print(f"Caught image capture exception: {ie}")
            try:
                self.resetConveyorBelt(firstIR, "Canceling paperfluidics and resetting conveyor belt", self.kit.stepper1)
            except Exception as ee:
                print(f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        except ImageAnalysisError as ia:
            print(f"Caught image analysis exception: {ia}")
            try:
                self.resetConveyorBelt(firstIR, "Canceling paperfluidics and resetting conveyor belt", self.kit.stepper1)
            except Exception as ee:
                print(f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
            
        
    def ArsenicDetection(self, key):
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
        
    def startMicroplasticDetection(self):
        print("Initiating Microplastics Thread")
        key = datetime.now().strftime("%F %T.%f")[:-3]
        microplasticThread = threading.Thread(target=self.microplasticDetection, args=(key,))
        microplasticThread.start()
        microplasticThread.join()
        
    def startInorganicsMetalDetection(self):
        print("Initiating Paperfluidic Thread")
        key = datetime.now().strftime("%F %T.%f")[:-3]
        microplasticThread = threading.Thread(target=self.InorganicsMetalDetection, args=(key,))
        microplasticThread.start()
        microplasticThread.join()
        
    def startArsenicDetection(self):
        print("Initiating Paperfluidic Thread")
        key = datetime.now().strftime("%F %T.%f")[:-3]
        microplasticThread = threading.Thread(target=self.ArsenicDetection, args=(key,))
        microplasticThread.start()
        microplasticThread.join()
    
    def startDetection(self):
        print("Initiating Water Baddies Detection")
        key = datetime.now().strftime("%F %T.%f")[:-3]
        
        threads = []
        
        threads.add(threading.Thread(target=self.InorganicsMetalDetection, args=(key,)))
        
        #threads.add(threading.Thread(target=self.microplasticDetection, args=(key,)))

        for thread in threads:
            thread.start()

        # threads.add(threading.Thread(target=self.ArsenicDetection, args=(key,)))

        
        for thread in threads:
            thread.join()

        print("Finished detection")

if __name__ == "__main__":
    wb = System()
    try:
        while True:
            continue
    except KeyboardInterrupt:
        BleTools.setDiscoverable(wb.bus, 0)
        wb.adv.unregister()
        wb.app.quit()
        wb.kit.stepper1.release()
        wb.kit.stepper1.release()
        wb.display.destroy()
        print("Motors released")
        
    

