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
from gpiozero import LED
from gpiozero import Button

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
        self.kit2 = MotorKit(address=0x61)
        self.cm_step = 31
        self.startBluetooth()
        self.display = DisplayHat(self.startMicroplasticDetection, self.startInorganicsMetalDetection, self.startDetection, self.restartBluetooth)

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
    
    def run_stepper(self, stepper_motor, steps, direction=stepper.FORWARD, style=stepper.SINGLE):
        for i in range(steps):
            stepper_motor.onestep(direction=direction, style=style)
            time.sleep(0.01)

    def resetConveyorBelt(self, ir, message, motor):
        print(message)
        detected = ir.is_object_detected()
        while (not detected):
#             print("Moving Conveyor Belt")
            self.run_stepper(motor, self.cm_step * 10)
            detected = ir.is_object_detected()
            detected = True

    def moveConveyorToSensor(self, targetIR, startIR, message, motor):
        print(message)
        detected = targetIR.is_object_detected()
        while (not detected):
#             print("Moving Conveyor Belt")
            self.run_stepper(motor, self.cm_step * 10)
            detected = targetIR.is_object_detected()
            detected = True
            startDetected = startIR.is_object_detected()
            if (startDetected):
                self.display.updateQueue({"warning":"Conveyor belt not supposed to be at start but is"})
                raise ConveyorGoAroundError("Conveyor belt at the start, although its not supposed to be.")
    
    def dispensePlasticWater(self):
        self.display.updateQueue({"stage":"Dispensing water"})
        print("Dispensing water")
        self.run_stepper(self.kit.stepper2, (self.cm_step * 8))
        return
    
    def captureMicroscopeImage(self):
        led = LED(19) #Blue spectrum LED
        led.on()
        cap = cv2.VideoCapture(8)
        if not cap.isOpened():
            self.display.updateQueue({"warning":"Error opening video stream or file"})
            print("Error opening video stream or file")
            raise Exception("Couldnt open microscope stream")
        
        ret, frame = cap.read()

        if not ret:
            self.display.updateQueue({"warning":"Can't receive frame (stream end?). Exiting ..."})
            print("Can't receive frame (stream end?). Exiting ...")
            raise Exception("Couldnt open microscope picture frame")
        
        path = f'plasticImages/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]}.png'
        cv2.imwrite(path, frame)
        led.off()
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
            self.display.updateQueue({"stage":"Resetting microplastic conveyor belt"})
            self.resetConveyorBelt(firstIR, "Resetting microplastic conveyor belt", self.kit.stepper1)
            time.sleep(2)
            sum = 0
            for i in range(1):
                print("Starting microplastic slide" + str(i+1))
                self.display.updateQueue({"stage":"Fetching microplastic slide and moving slide under dropper"})
                self.moveConveyorToSensor(dropperIR, firstIR, "Fetching microplastic slide and moving slide under dropper", self.kit.stepper1)
                time.sleep(2)
                self.dispensePlasticWater()
                time.sleep(2)
                self.display.updateQueue({"stage":"Moving microplastic slide under microscope"})
                self.moveConveyorToSensor(microscopeIR, firstIR, "Moving microplastic slide under microscope", self.kit.stepper1)
                time.sleep(2)
                try:
                    #imagePath = self.captureMicroscopeImage()
                    #print(f"Microplastic image path: {imagePath}")
                    print("Hello")
                except Exception as e:
                    self.display.updateQueue({"warning":f"Error during image capture: {e}"})
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing image from the micropscope. Canceling microplastic job!")

                try:    
                    testImagePath = "./test_images/Snap_027.jpg"
                    quantity = microplastic_concentration(testImagePath)
                    #quantity = microplastic_concentration(imagePath)
                except Exception as e:
                    self.display.updateQueue({"warning":f"Error during image analysis: {e}"})
                    print(f"Error during image analysis: {e}")
                    raise ImageCaptureError("Error during capturing image from the micropscope. Canceling microplastic job!")
                
                sum += quantity

            concentration = sum
            
            mpChar = self.getCharacteristic("Microplastic")
            if (mpChar):
                mpChar.WriteValue(str(concentration))
                print("Updated value:"+ str(concentration))
                
                self.updateKey(key)
            else:
                print("Microplastic characteristic not found")

            self.display.updateQueue({"stage": "Bluetooth Uploaded.  Resetting conveyor belt"})
            self.resetConveyorBelt(firstIR, "Resetting conveyor belt", self.kit.stepper1)
            
            self.display.updateQueue({"stage": "Microplastic Detection Finished"})
        except Exception as e:
            self.display.updateQueue({"warning":f"Error during image analysis: {e}"})
            print(f"Caught exception: {e}")
            try:
                self.display.updateQueue({"stage":"Cancelling microplastic detection and discarding any active trays"})
                self.resetConveyorBelt(firstIR, "Cancelling microplastic detection and discarding any active trays", self.kit.stepper1)
            except Exception as ee:
                self.display.updateQueue({"warning":f"Fatal error while canceling microplastic detection, after an error had already occured. FATAL ERROR: {ee}"})
                print(f"Fatal error while canceling microplastic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        except ImageCaptureError as ie:
            print(f"Caught image capture exception: {ie}")
            try:
                self.display.updateQueue({"stage":"Cancelling microplastic detection and discarding any active trays"})
                self.resetConveyorBelt(firstIR, "Cancelling microplastic detection and discarding any active trays", self.kit.stepper1)
            except Exception as ee:
                self.display.updateQueue({"warning":f"Fatal error while canceling microplastic detection, after an error had already occured. FATAL ERROR: {ee}"})
                print(f"Fatal error while canceling microplastic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        except ImageAnalysisError as ia:
            print(f"Caught image analysis exception: {ia}")
            try:
                self.display.updateQueue({"stage":"Cancelling microplastic detection and discarding any active trays"})
                self.resetConveyorBelt(firstIR, "Cancelling microplastic detection and discarding any active trays", self.kit.stepper1)
            except Exception as ee:
                self.display.updateQueue({"warning":f"Fatal error while canceling microplastic detection, after an error had already occured. FATAL ERROR: {ee}"})
                print(f"Fatal error while canceling microplastic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        finally:
            self.display.plasticActive = False

    def capturePiImage(self):
        led = LED(40)
        led.on()
        time.sleep(0.5)
        picam = Picamera2()
        picam.configure(picam.create_still_configuration())
        picam.start()
        picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        path = f'paperFluidicImages/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]}.png'
        picam.capture_file(path)
        picam.close()
        led.off()
        return path
        
    def dispenseFluidicWater(self):
        self.display.updateQueue({"stage":"Dispensing Paperfluidics water"})
        print("Dispensing Paperfluidicswater")
        self.run_stepper(self.kit2.stepper2, (self.cm_step * 8))
        return
                
    def InorganicsMetalDetection(self, key):
        try:
            firstIR = IRSensor(14)
            dropperIR = IRSensor(18)
            microscopeIR = IRSensor(23)
            self.display.updateQueue({"stage":"Resetting paperfluidic conveyor belt"})
            self.resetConveyorBelt(firstIR, "Resetting paperfluidic conveyor belt", self.kit2.stepper1)
            time.sleep(2)
            self.display.updateQueue({"stage":"Fetching paperfluidics and moving the slide under the water dropper"})
            self.moveConveyorToSensor(dropperIR, firstIR, "Fetching paperfluidics and moving the slide under the water dropper", self.kit2.stepper1)
            time.sleep(2)
            self.dispenseFluidicWater()
            time.sleep(2)
            self.display.updateQueue({"stage":"Moving paperluidics under the camera"})
            self.moveConveyorToSensor(microscopeIR, firstIR, "Moving paperluidics under the camera", self.kit2.stepper1)
            try:
                imagePath = self.capturePiImage()
                print(f"First paperfluidics image: {imagePath}")
                self.display.updateQueue({"stage":"Waiting for lead reaction"})
                print("Waiting for lead reaction")
                time.sleep(3)
                leadImagePath = self.capturePiImage() #Just capture lead image
                print(f"Lead paperfluidics image: {leadImagePath}")

                #Just for testing
                testImagePath = "./test_images/paperfluidic.jpg"
                testLeadImagePath = "./test_images/paperfluidic_test.jpg"
            except Exception as e:
                    self.display.updateQueue({"warning":f"Error during image capture: {e}"})
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing image from the PiCamera for lead or base image. Canceling paperfluidics job!")
            
            try:
                #leadConcentration = paperfluidic_concentration(imagePath, leadImagePath)['lead']
                self.display.updateQueue({"stage":"Starting Lead Concentration Analysis"})
                print("Starting Lead Concentration Analysis")
                vals = pfa.paperfluidic_concentration(testImagePath, testLeadImagePath)
                leadConcentration = vals['Lead']
            except Exception as e:
                self.display.updateQueue({"warning":f"Error during image analysis: {e}"})
                print(f"Error during image analysis: {e}")
                raise ImageCaptureError("Error analyzing lead image. Canceling paperfluidics job!")
            
            self.display.updateQueue({"stage":"Waiting for paperfluidic reactions"})
            print("Waiting for paperfluidic reactions")
            time.sleep(5)

            try:
                finalImagePath = self.capturePiImage()
                print(f"Final paperfluidics image: {finalImagePath}")
                
                testFinalImagePath = "./test_images/paperfluidic_test.jpg"
            except Exception as e:
                self.display.updateQueue({"warning":f"Error during image capture: {e}"})
                print(f"Error during image capture: {e}")
                raise ImageCaptureError("Error during capturing final image from the PiCamera. Canceling paperfluidics job!")
            
            try:
                #concentration = paperfluidic_concentration(imagePath, finalImagePath)
                concentration = pfa.paperfluidic_concentration(testImagePath, testFinalImagePath)
                concentration['Lead'] = leadConcentration
            except Exception as e:
                self.display.updateQueue({"warning":f"Error during image capture: {e}"})
                print(f"Error during image capture: {e}")
                raise ImageCaptureError("Error during capturing image from the PiCamera. Canceling paperfluidics job!")

            leadChar = self.getCharacteristic("Lead")
            if (leadChar):
                leadChar.WriteValue(str(concentration["Lead"]))
                print("Updated value:"+ str(concentration["Lead"]))
                
                self.updateKey(key)
            else:
                print("Lead characteristic not found")

            mercuryChar = self.getCharacteristic("Mercury")
            if (mercuryChar):
                mercuryChar.WriteValue(str(concentration["Mercury"]))
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

            phosphateChar = self.getCharacteristic("Phosphate")
            if (phosphateChar):
                phosphateChar.WriteValue(str(concentration["Phosphate"]))
                print("Updated value:"+ str(concentration["Phosphate"]))
                
                self.updateKey(key)
            else:
                print("Phosphate characteristic not found")
            
            self.display.updateQueue({"stage":"Resetting the paperfludics conveyor belt"})
            self.resetConveyorBelt(firstIR, "Bluetooth Uploaded. Resetting the paperfludics conveyor belt", self.kit2.stepper1)

            self.display.updateQueue({"stage": "Inorganics and Metal Detection Finished"})
        except Exception as e:
            print(f"Caught exception: {e}")
            try:
                self.display.updateQueue({"warning":"Canceling paperfluidics and resetting conveyor belt"})
                self.resetConveyorBelt(firstIR, "Canceling paperfluidics and resetting conveyor belt", self.kit.stepper1)
            except Exception as ee:
                self.display.updateQueue({"warning":f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}"})
                print(f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        except ImageCaptureError as ie:
            print(f"Caught image capture exception: {ie}")
            try:
                self.display.updateQueue({"warning":"Canceling paperfluidics and resetting conveyor belt"})
                self.resetConveyorBelt(firstIR, "Canceling paperfluidics and resetting conveyor belt", self.kit.stepper1)
            except Exception as ee:
                self.display.updateQueue({"warning":f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}"})
                print(f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        except ImageAnalysisError as ia:
            print(f"Caught image analysis exception: {ia}")
            try:
                self.display.updateQueue({"warning":"Canceling paperfluidics and resetting conveyor belt"})
                self.resetConveyorBelt(firstIR, "Canceling paperfluidics and resetting conveyor belt", self.kit.stepper1)
            except Exception as ee:
                self.display.updateQueue({"warning":f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}"})
                print(f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        finally:
            self.display.paperActive = False
    
    def isDoorClosed():
        try:
            button = Button(4)
            return button.is_pressed
        except Exception as e:
            print(f"Error checking door status: {e}")
            return None

        
    def startMicroplasticDetection(self):
        self.display.updateQueue({"stage":"Initiating Microplastic Detection"})
        print("Initiating Microplastic Detection")
        key = datetime.now().strftime("%F %T.%f")[:-3]
        mpThread = threading.Thread(target=self.microplasticDetection, args=(key,))
        mpThread.start()
        mpThread.join()
        time.sleep(10)

    def startInorganicsMetalDetection(self):
        self.display.updateQueue({"stage":"Initiating Inorganics Metal Detection"})
        print("Initiating Inorganics Metal Detection")
        key = datetime.now().strftime("%F %T.%f")[:-3]
        pfThread = threading.Thread(target=self.InorganicsMetalDetection, args=(key,))
        pfThread.start()
        pfThread.join()
        time.sleep(10)

    def startDetection(self):
        self.display.updateQueue({"stage":"Initiating All Detections in Parallel"})
        print("Initiating All Detections in Parallel")
        key = datetime.now().strftime("%F %T.%f")[:-3]

        # Submit all three processes in parallel
        threads = [
            threading.Thread(target=self.microplasticDetection, args=(key,)),
            threading.Thread(target=self.InorganicsMetalDetection, args=(key,)),
        ]
        
        for thread in threads:
            thread.start()

        self.display.updateQueue({"stage":"All detections started. Waiting for results in background."})
        print("All detections started. Waiting for results in background.")
        
        for thread in threads:
            thread.join()
        
if __name__ == "__main__":
    wb = System()
    try:
        while True:
            continue
    except KeyboardInterrupt:
        print("Shutting down processes...")
        wb.executor.shutdown(wait=True)  # Ensure all processes exit
        BleTools.setDiscoverable(wb.bus, 0)
        wb.adv.unregister()
        wb.app.quit()
        wb.kit.stepper1.release()
        wb.kit.stepper1.release()
        wb.display.destroy()
        print("Motors released. System shut down cleanly.")

        
    

