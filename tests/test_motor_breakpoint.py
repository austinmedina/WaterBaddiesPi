from breakpointSensor import IRSensor
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
import time

def test_plastic_motor_breakpoint():
    kit = MotorKit()
    firstIR = IRSensor(26)
    dropperIR = IRSensor(20)
    microscopeIR = IRSensor(12)

    resetConveyorBelt(firstIR, "Resetting paperfluidics conveyor belt", kit.stepper1)
    time.sleep(1)
    moveConveyorToSensor(dropperIR, firstIR, "Fetching paperfluidics slide and moving slide under dropper", kit.stepper1)
    time.sleep(1)
    moveConveyorToSensor(microscopeIR, firstIR, "Moving paperfluidics slide under camera", kit.stepper1)
    time.sleep(1)
    resetConveyorBelt(firstIR, "Resetting conveyor belt", kit.stepper1)

def test_plastic_motor_breakpoint():
    kit2 = MotorKit(address=0x61)
    firstIR = IRSensor(26)
    dropperIR = IRSensor(20)
    cameraIR = IRSensor(12)

    resetConveyorBelt(firstIR, "Resetting microplastic conveyor belt", kit2.stepper1)
    time.sleep(1)
    moveConveyorToSensor(dropperIR, firstIR, "Fetching microplastic slide and moving slide under dropper", kit2.stepper1)
    time.sleep(1)
    moveConveyorToSensor(cameraIR, firstIR, "Moving microplastic slide under microscope", kit2.stepper1)
    time.sleep(1)
    resetConveyorBelt(firstIR, "Resetting conveyor belt", kit2.stepper1)

def run_stepper(stepper_motor, steps, direction=stepper.FORWARD, style=stepper.SINGLE):
        for i in range(steps):
            stepper_motor.onestep(direction=direction, style=style)
            time.sleep(0.01)

def resetConveyorBelt(ir, message, motor):
    print(message)
    detected = ir.is_object_detected()
    while (not detected):
        run_stepper(motor, 300)
        detected = ir.is_object_detected()
        detected = True

def moveConveyorToSensor(self, targetIR, startIR, message, motor):
    print(message)
    detected = targetIR.is_object_detected()
    while (not detected):
        run_stepper(motor, 300)
        detected = targetIR.is_object_detected()
        detected = True
        startDetected = startIR.is_object_detected()
        if (startDetected):
            raise Exception("Conveyor belt at the start, although its not supposed to be.")
