from gpiozero import Button

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
    
