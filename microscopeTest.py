import cv2
from datetime import datetime
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
from breakpointSensor import IRSensor
import time
from gpiozero import LED

def run_stepper(stepper_motor, cm=1, direction=stepper.BACKWARD, style=stepper.DOUBLE):
    steps = cm
    for i in range(steps):
        stepper_motor.onestep(direction=direction, style=style)
        time.sleep(0.01)
        
kit2 = MotorKit(address=0x61)
microscopeIR = IRSensor(20)
detected = microscopeIR.is_object_detected()

plasticLED = LED(19)
#         if (isSecondIR and not detected): #To ensure the slide makes is off the dispenser
#             self.run_stepper(motor, 130)
#         detected = targetIR.is_object_detected()
while (not detected):
    run_stepper(kit2.stepper2, 1)
    detected = microscopeIR.is_object_detected()

kit2.stepper2.release()

# plasticLED.on()
# # Initialize the camera
# cap = cv2.VideoCapture(8)  # 0 usually refers to the first USB camera

# # Check if the camera is opened successfully
# if not cap.isOpened():
#     print("Error opening video stream or file")

# while True:
#     # Capture frame-by-frame
#     ret, frame = cap.read()

#     # If frame is read correctly, ret is True
#     if not ret:
#         print("Can't receive frame (stream end?). Exiting ...")
#         break

#     # Display the resulting frame
#     cv2.imshow('frame', frame)
    
#     #save the image
#     #cv2.imwrite(f'plasticImages/{datetime.now().strftime("%F %T.%f")[:-3]}.png', frame)

#     # Press 'q' to exit
#     if cv2.waitKey(1) == ord('q'):
#         break

#     time.sleep(1)

# # When everything done, release the capture
# plasticLED.off()
# cap.release()
# cv2.destroyAllWindows()

plasticLED.on()
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
plasticLED.off() 