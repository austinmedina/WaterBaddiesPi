from gpiozero import Button
from signal import pause

class IRSensor:
    def __init__(self, pin):
        ir_sensor = Button(pin)
        ir_sensor.when_pressed = on_ir_detected
        ir_sensor.when_released = on_ir_cleared
        
    def on_ir_detected():
        return
        print("IR Sensor Detected an Object!")
    
    def on_ir_cleared():
        print("IR Sensor Cleared (No Object Detected)")
    
    def is_object_detected():
    if ir_sensor.value:
        print("Object detected!")
        return True
    else:
        print("No object detected!")
        return False
    
