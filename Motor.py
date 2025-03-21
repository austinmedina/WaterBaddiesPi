import time
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

# Initialize the Motor HAT
kit = MotorKit()
kit2 = MotorKit(address=0x61)
cm_step = 31  # Approx. # of steps to move a centimeter


# Function to run a stepper motor
def run_stepper(stepper_motor, steps, direction=stepper.FORWARD, style=stepper.SINGLE):
    for i in range(steps):
        stepper_motor.onestep(direction=direction, style=style)
        time.sleep(0.01)  # Adjust delay for speed


# def run_both_motors(steps, direction=stepper.FORWARD, style=stepper.SINGLE):
#     for _ in range(steps):
#         kit.stepper1.onestep(direction=direction, style=style)
#         # kit.stepper2.onestep(direction=direction, style=style)
#         time.sleep(0.01)  # Adjust delay for speed


# Test Stepper Motor 1 (M1 & M2)
# print("Running Stepper Motor 1")
# run_stepper(kit.stepper1, cm_step*5)  # 31 steps forward
# 
# # Test Stepper Motor 2 (M3 & M4)
# print("Running Stepper Motor 2")
# run_stepper(kit.stepper2, cm_step*5, direction=stepper.FORWARD)

print("Running Stepper Motor 3")
run_stepper(kit2.stepper1, cm_step*5)

# print("Running Stepper Motor 4")
# run_stepper(kit2.stepper2, cm_step*5)

# print("Running both motors...")
# run_both_motors(cm_step)

# Release both stepper motors
kit.stepper1.release()
kit.stepper2.release()
kit2.stepper1.release()
kit2.stepper2.release()
print("Motors released")