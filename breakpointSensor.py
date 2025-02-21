from gpiozero import Button
from signal import pause
import time

class IRSensor:
    def __init__(self, pin):
        self.ir_sensor = Button(pin)
    
    def is_object_detected(self):
        if self.ir_sensor.value:
            #print("Object detected!")
            return True
        else:
            #print("No object detected!")
            return False
        
if __name__ == "__main__":
    firstIR = IRSensor(26)
    dropperIR = IRSensor(20)
    microscopeIR = IRSensor(12)
    
    print(f"First motor: {firstIR.is_object_detected()}")
    print(f"Dropper sensor: {dropperIR.is_object_detected()}")
    print(f"Camera sensor: {microscopeIR.is_object_detected()}")
    
