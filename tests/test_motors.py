from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
import time

def test_kit1():
    kit = MotorKit()
#     run_stepper(kit.stepper1)
#     time.sleep(0.5)
    run_stepper(kit.stepper2)
    kit.stepper1.release()
    kit.stepper2.release()

# def test_kit2():
#     kit2 = MotorKit(address=0x61)
#     run_stepper(kit2.stepper1)
#     time.sleep(0.5)
#     run_stepper(kit2.stepper2, 1000)
#     kit2.stepper1.release()
#     kit2.stepper2.release()

def run_stepper(stepper_motor, cm=31, direction=stepper.BACKWARD, style=stepper.DOUBLE):
    steps = cm * 6
    for i in range(steps):
        stepper_motor.onestep(direction=direction, style=style)
        time.sleep(0.01)