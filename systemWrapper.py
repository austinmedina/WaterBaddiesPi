from bluetoothCreation.baddiesDetection import BaddiesAdvertisement, BaddiesDetectionService, BluetoothAgent
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
import cv2

from breakpointSensor import IRSensor
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
from gpiozero import LED
from gpiozero import Button

import paperfluidic_analysis as pfa
from microscope_analysis import microplastic_concentration

from DisplayHAT import DisplayHat

AGENT_PATH = "/com/example/agent"

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
        self.releaseMotors()
        self.cm_step = 31
        self.firstIR = IRSensor(23)
        self.dropperIR = IRSensor(18)
        self.microscopeIR = IRSensor(14)
        
        self.PlasticFirstIR = IRSensor(12)
        self.PlasticDropperIR = IRSensor(26)
        self.PlsticMicroscopeIR = IRSensor(20)
        
        self.plasticLED = LED(19)
        self.paperLED = LED(21)
        
        self.startBluetooth()
        self.display = DisplayHat(self.startMicroplasticDetection, self.startInorganicsMetalDetection, self.startDetection, self.restartBluetooth, self.startDemo)

    def startBluetooth(self):

        BleTools.power_adapter(self.bus)
        BleTools.setDiscoverable(self.bus, 1)
        
        self.agent = BluetoothAgent(self.bus, AGENT_PATH)
        agent_manager = dbus.Interface(
            self.bus.get_object("org.bluez", "/org/bluez"),
            "org.bluez.AgentManager1"
        )
        agent_manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")
        agent_manager.RequestDefaultAgent(AGENT_PATH)

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
        
    def releaseMotors(self):
        self.kit.stepper1.release()
        self.kit.stepper2.release()
        self.kit2.stepper1.release()
        self.kit2.stepper2.release()
    
    def run_stepper(self, stepper_motor, steps, direction=stepper.FORWARD, style=stepper.DOUBLE):
        for i in range(steps):
            stepper_motor.onestep(direction=direction, style=style)
            time.sleep(0.01)

    def resetConveyorBelt(self, ir, message, motor):
        print(message)
        detected = ir.is_object_detected()
        while (not detected):
            self.run_stepper(motor, 15)
            detected = ir.is_object_detected()
            print(detected)
        
        self.releaseMotors()

    def moveConveyorToSensor(self, targetIR, startIR, message, motor, isSecondIR=False):
        detected = targetIR.is_object_detected()
#         if (isSecondIR and not detected): #To ensure the slide makes is off the dispenser
#             self.run_stepper(motor, 130)
#         detected = targetIR.is_object_detected()
        while (not detected):
            self.run_stepper(motor, 20)
            detected = targetIR.is_object_detected()
#             startDetected = startIR.is_object_detected()
#             if (startDetected):
#                 self.display.updateQueue({"warning":"Conveyor belt not supposed to be at start but is"})
#                 raise ConveyorGoAroundError("Conveyor belt at the start, although its not supposed to be.")
        self.releaseMotors()
    
    def dispensePlasticWater(self):
        self.display.updateQueue({"stage":"Dispensing water"})
        print("Dispensing water")
        self.run_stepper(self.kit.stepper2, (90), stepper.BACKWARD)
        return
    
    def captureMicroscopeImage(self):
        self.paperLED.on()
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
        self.paperLED.off()
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
            self.display.updatePercentage(1)
            firstIR = self.PlasticFirstIR
            dropperIR = self.PlasticDropperIR
            microscopeIR = self.PlsticMicroscopeIR
            self.display.updatePercentage(2)
            self.display.updateQueue({"stage":"Resetting microplastic conveyor belt"})
            self.resetConveyorBelt(firstIR, "Resetting microplastic conveyor belt", self.kit.stepper1)
            self.display.updatePercentage(10)
            time.sleep(2)
            sum = 0
            loop_counter = 0
            percent_increase = 75 / (5 * 5) #(starting percentage - ending) / (Stages per loop * loops)

            for i in range(5):
                print("Starting microplastic slide" + str(i+1))
                self.display.updateQueue({"stage":"Fetching microplastic slide and moving slide under dropper"})
                self.moveConveyorToSensor(dropperIR, firstIR, "Fetching microplastic slide and moving slide under dropper", self.kit.stepper1, True)
                loop_counter += 1
                new_pct = 10 + round(loop_counter * percent_increase)
                self.display.updatePercentage(int(new_pct))
                time.sleep(2)
                self.dispensePlasticWater()
                loop_counter += 1
                new_pct = 10 + round(loop_counter * percent_increase)
                self.display.updatePercentage(int(new_pct))
                time.sleep(2)
                self.display.updateQueue({"stage":"Moving microplastic slide under microscope"})
                self.moveConveyorToSensor(microscopeIR, firstIR, "Moving microplastic slide under microscope", self.kit.stepper1)
                loop_counter += 1
                new_pct = 10 + round(loop_counter * percent_increase)
                self.display.updatePercentage(int(new_pct))
                time.sleep(2)
                try:
                    #imagePath = self.captureMicroscopeImage()
                    #print(f"Microplastic image path: {imagePath}")
                    loop_counter += 1
                    new_pct = 10 + round(loop_counter * percent_increase)
                    self.display.updatePercentage(int(new_pct))
                except Exception as e:
                    self.display.updateQueue({"warning":f"Error during image capture: {e}"})
                    print(f"Error during image capture: {e}")
                    raise ImageCaptureError("Error during capturing image from the micropscope. Canceling microplastic job!")

                try:    
                    testImagePath = "./test_images/Snap_027.jpg"
                    quantity = microplastic_concentration(testImagePath)
                    #quantity = microplastic_concentration(imagePath)
                    loop_counter += 1
                    new_pct = 10 + round(loop_counter * percent_increase)
                    self.display.updatePercentage(int(new_pct))
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
                self.display.updatePercentage(95)
            else:
                print("Microplastic characteristic not found")

            self.display.updateQueue({"stage": "Bluetooth Uploaded.  Resetting conveyor belt"})
            self.resetConveyorBelt(firstIR, "Resetting conveyor belt", self.kit.stepper1)
            self.display.updatePercentage(100)
            
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
            self.releaseMotors()
            
    def capture_image_with_timeout(self, picam, path, timeout=20):
        def _capture():
            try:
                picam.capture_file(path)
            except Exception as e:
                print("Capture error:", e)

        thread = threading.Thread(target=_capture)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            print("Capture timed out!")
            return False
        return True

    def capturePiImage(self):
        self.paperLED.on()
        time.sleep(1)
        picam = Picamera2()
        picam.configure(picam.create_still_configuration())
        picam.start()
        picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        path = f'paperFluidicImages/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]}.png'
        success = self.capture_image_with_timeout(picam, path, timeout=5)
        picam.close()
        self.paperLED.off()
        print("LED off")
        if not success:
            raise RuntimeError("Camera capture timed out")
        return path

        
    def dispenseFluidicWater(self):
        self.display.updateQueue({"stage":"Dispensing Paperfluidics water"})
        print("Dispensing Paperfluidicswater")
        self.run_stepper(self.kit2.stepper2, (90), direction=stepper.BACKWARD)
        return
                
    def InorganicsMetalDetection(self, key):
        try:
            self.display.updatePercentage(1)
            firstIR = self.firstIR
            dropperIR = self.dropperIRs
            microscopeIR = self.microscopeIR
            self.display.updateQueue({"stage": "Resetting paperfluidic conveyor belt"})
            self.resetConveyorBelt(firstIR, "Resetting paperfluidic conveyor belt", self.kit2.stepper1)
            self.display.updatePercentage(5)
            time.sleep(2)

            self.display.updateQueue({"stage": "Fetching paperfluidics and moving the slide under the water dropper"})
            self.moveConveyorToSensor(dropperIR, firstIR, "Fetching paperfluidics and moving the slide under the water dropper", self.kit2.stepper1, True)
            self.display.updatePercentage(10)
            time.sleep(2)

            self.dispenseFluidicWater()
            self.display.updatePercentage(20)
            time.sleep(2)

            self.display.updateQueue({"stage": "Moving paperluidics under the camera"})
            self.moveConveyorToSensor(microscopeIR, firstIR, "Moving paperluidics under the camera", self.kit2.stepper1)
            self.display.updatePercentage(30)

            try:
                self.display.updateQueue({"stage": "Waiting for reactions"})
                self.display.updatePercentage(32.5)
                print("Waiting for reactions")
                time.sleep(3) #Will be 120 seconds
                leadImagePath = self.capturePiImage() #Capture image of peperfluidics
                self.display.updatePercentage(37.5)
                print(f"Lead paperfluidics image: {leadImagePath}")

                # Just for testing
                testImagePath = "./test_images/paperfluidic_test.jpg"
            except Exception as e:
                self.display.updateQueue({"warning": f"Error during image capture: {e}"})
                print(f"Error during image capture: {e}")
                raise ImageCaptureError("Error during capturing image from the PiCamera for lead or base image. Canceling paperfluidics job!")

            try:
                self.display.updateQueue({"stage": "Starting Lead Concentration Analysis"})
                print("Starting Concentration Analysis")
                vals = pfa.paperfluidic_concentration(testImagePath)
                self.display.updatePercentage(45)
            except Exception as e:
                self.display.updateQueue({"warning": f"Error during image analysis: {e}"})
                print(f"Error during image analysis: {e}")
                raise ImageCaptureError("Error analyzing lead image. Canceling paperfluidics job!")

            leadChar = self.getCharacteristic("Lead")
            if leadChar:
                leadChar.WriteValue(str(concentration["Lead"]))
                print("Updated value:" + str(concentration["Lead"]))
                self.updateKey(key)
                self.display.updatePercentage(75)
            else:
                print("Lead characteristic not found")

            nitriteChar = self.getCharacteristic("Nitrite")
            if nitriteChar:
                nitriteChar.WriteValue(str(concentration["Nitrite"]))
                print("Updated value:" + str(concentration["Nitrite"]))
                self.updateKey(key)
                self.display.updatePercentage(80)
            else:
                print("Nitrite characteristic not found")

            cadmiumChar = self.getCharacteristic("Cadmium")
            if cadmiumChar:
                cadmiumChar.WriteValue(str(concentration["Cadmium"]))
                print("Updated value:" + str(concentration["Cadmium"]))
                self.updateKey(key)
                self.display.updatePercentage(85)
            else:
                print("Cadmium characteristic not found")

            nitrateChar = self.getCharacteristic("Nitrate")
            if nitrateChar:
                nitrateChar.WriteValue(str(concentration["Nitrate"]))
                print("Updated value:" + str(concentration["Nitrate"]))
                self.updateKey(key)
                self.display.updatePercentage(90)
            else:
                print("Nitrate characteristic not found")

            phosphateChar = self.getCharacteristic("Phosphate")
            if phosphateChar:
                phosphateChar.WriteValue(str(concentration["Phosphate"]))
                print("Updated value:" + str(concentration["Phosphate"]))
                self.updateKey(key)
                self.display.updatePercentage(95)
            else:
                print("Phosphate characteristic not found")

            self.display.updateQueue({"stage": "Resetting the paperfludics conveyor belt"})
            self.resetConveyorBelt(firstIR, "Bluetooth Uploaded. Resetting the paperfludics conveyor belt", self.kit2.stepper1)
            self.display.updatePercentage(100)

            self.display.updateQueue({"stage": "Inorganics and Metal Detection Finished"})
        except Exception as e:
            print(f"Caught exception: {e}")
            try:
                self.display.updateQueue({"warning": "Canceling paperfluidics and resetting conveyor belt"})
                self.resetConveyorBelt(firstIR, "Canceling paperfluidics and resetting conveyor belt", self.kit.stepper1)
            except Exception as ee:
                self.display.updateQueue({"warning": f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}"})
                print(f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        except ImageCaptureError as ie:
            print(f"Caught image capture exception: {ie}")
            try:
                self.display.updateQueue({"warning": "Canceling paperfluidics and resetting conveyor belt"})
                self.resetConveyorBelt(firstIR, "Canceling paperfluidics and resetting conveyor belt", self.kit.stepper1)
            except Exception as ee:
                self.display.updateQueue({"warning": f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}"})
                print(f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        except ImageAnalysisError as ia:
            print(f"Caught image analysis exception: {ia}")
            try:
                self.display.updateQueue({"warning": "Canceling paperfluidics and resetting conveyor belt"})
                self.resetConveyorBelt(firstIR, "Canceling paperfluidics and resetting conveyor belt", self.kit.stepper1)
            except Exception as ee:
                self.display.updateQueue({"warning": f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}"})
                print(f"Fatal error while canceling paperfluidic detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        finally:
            self.display.updateQueue({"stage": "Paperfluidics Detection Finished"})
            self.display.updatePercentage(100)
            self.display.paperActive = False
            self.releaseMotors()

    def demoSystem(self, key):
        try:
            self.display.updatePercentage(1)
            firstIR = self.firstIR
            dropperIR = self.dropperIR
            microscopeIR = self.microscopeIR
            self.display.updatePercentage(5)
            self.display.updateQueue({"stage": "Resetting demo conveyor belt"})
            self.resetConveyorBelt(firstIR, "Resetting demo conveyor belt", self.kit.stepper1)
            self.display.updatePercentage(10)
            time.sleep(2)

            loop_counter = 0
            percent_increase = 65 / (3 * 1) #(starting percentage - ending) / (Stages per loop * loops)
            for i in range(1):
                print("Starting demo slide " + str(i + 1))
                self.display.updateQueue({"stage": "Fetching demo slide and moving slide under dropper"})
                self.moveConveyorToSensor(dropperIR, firstIR, "Fetching demo slide and moving slide under dropper", self.kit.stepper1, True)
                loop_counter += 1
                new_pct = 10 + round(loop_counter * percent_increase)
                self.display.updatePercentage(int(new_pct))
                self.dispensePlasticWater()
                loop_counter += 1
                new_pct = 10 + round(loop_counter * percent_increase)
                self.display.updatePercentage(int(new_pct))
                self.display.updateQueue({"stage": "Moving demo slide under microscope"})
                self.moveConveyorToSensor(microscopeIR, firstIR, "Moving demo slide under camera", self.kit.stepper1)
                loop_counter += 1
                new_pct = 10 + round(loop_counter * percent_increase)
                self.display.updatePercentage(int(new_pct))
#                 self.capturePiImage()
                time.sleep(2)

            concentration = 1.2
            mpChar = self.getCharacteristic("Microplastic")
            if mpChar:
                mpChar.WriteValue(str(concentration))
                print("Updated value:" + str(concentration))
                self.updateKey(key)
                self.display.updatePercentage(80)
            else:
                print("Microplastic characteristic not found")
                self.display.updatePercentage(75)

            self.display.updateQueue({"stage": "Bluetooth Uploaded.  Resetting conveyor belt"})
            self.resetConveyorBelt(firstIR, "Resetting conveyor belt", self.kit.stepper1)
            self.display.updatePercentage(90)
        except Exception as e:
            self.display.updateQueue({"warning": f"Error: {e}"})
            print(f"Caught exception: {e}")
            try:
                self.display.updateQueue({"stage": "Cancelling demo detection and discarding any active trays"})
                self.resetConveyorBelt(firstIR, "Cancelling demo detection and discarding any active trays", self.kit.stepper1)
            except Exception as ee:
                self.display.updateQueue({"warning": f"Fatal error while canceling demo detection, after an error had already occured. FATAL ERROR: {ee}"})
                print(f"Fatal error while canceling demo detection, after an error had already occured. FATAL ERROR: {ee}")
            return
        finally:
            self.display.updateQueue({"stage": "demo Detection Finished"})
            self.display.updatePercentage(100)
            self.display.demoActive = False
            self.releaseMotors()
    
    def isDoorClosed(self):
        try:
            button = Button(4)
            return button.is_pressed
        except Exception as e:
            print(f"Error checking door status: {e}")
            return None
        
    def startDemo(self):
        self.display.updateQueue({"stage":"Initiating Demo Detection"})
        print("Initiating Demo Detection")
        key = datetime.now().strftime("%F %T.%f")[:-3]
        demoThread = threading.Thread(target=self.demoSystem, args=(key,))
        demoThread.start()
        
    def startMicroplasticDetection(self):
        self.display.updateQueue({"stage":"Initiating Microplastic Detection"})
        print("Initiating Microplastic Detection")
        key = datetime.now().strftime("%F %T.%f")[:-3]
        mpThread = threading.Thread(target=self.microplasticDetection, args=(key,))
        mpThread.start()

    def startInorganicsMetalDetection(self):
        self.display.updateQueue({"stage":"Initiating Inorganics Metal Detection"})
        print("Initiating Inorganics Metal Detection")
        key = datetime.now().strftime("%F %T.%f")[:-3]
        pfThread = threading.Thread(target=self.InorganicsMetalDetection, args=(key,))
        pfThread.start()

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

        
    

