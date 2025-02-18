from gpiozero import Button
from signal import pause
import time

class IRSensor:
    def __init__(self, pin):
        self.ir_sensor = Button(pin)
    
    def is_object_detected(self):
        if self.ir_sensor.value:
            print("Object detected!")
            return True
        else:
            print("No object detected!")
            return False
        
if __name__ == "__main__":
    ir = IRSensor(26)
    while True:
        print(ir.is_object_detected())
    
