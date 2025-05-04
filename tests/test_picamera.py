import os
import time
from gpiozero import LED
from picamera2 import Picamera2
from libcamera import controls
from datetime import datetime

# def test_picamera():
#     os.makedirs("paperFluidicImages", exist_ok=True)
#     picam = Picamera2()
#     picam.configure(picam.create_still_configuration())
#     picam.start()
#     picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
#     path = f'paperFluidicImages/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]}.png'
#     picam.capture_file(path)
#     picam.close()
# 
#     assert os.path.exists(path), f"File {path} was not created"

# def test_with_leds():
#     os.makedirs("paperFluidicImages", exist_ok=True)
# 
#     picam = Picamera2()
#     picam.configure(picam.create_still_configuration())
#     picam.start()
# 
#     # trigger a single autofocus cycle
#     picam.set_controls({
#         "AfMode":    controls.AfModeEnum.Single,
#         "AfTrigger": controls.AfTriggerEnum.Start
#     })
# 
#     # give the AF algorithm a moment to converge
#     time.sleep(1)
#     path = f'paperFluidicImages/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]}.png'
#     picam.capture_file(path)
#     picam.close()
# 
#     print(path)
#     assert os.path.exists(path), f"File {path} was not created"
# 
# if __name__=="__main__":
#     test_with_leds()
    
#!/usr/bin/env python3
from picamera2 import Picamera2
from libcamera import controls
from datetime import datetime
import os

def auto_focus_capture(output_dir="images"):
    os.makedirs(output_dir, exist_ok=True)
    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration())
    picam2.start()
    if not picam2.autofocus_cycle():
        print("Warning: autofocus failed, capturing anyway")
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.jpg")
    path = os.path.join(output_dir, filename)
    picam2.capture_file(path)
    picam2.stop()
    print(f"Saved image to {path}")

if __name__ == "__main__":
    auto_focus_capture()

