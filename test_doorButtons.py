from gpiozero import LED, Button
import time

#button = Button(4)
button = Button(15)
#led1 = LED(8)
# led2 = LED(19)
try:
	while True:
		if button.is_pressed:
			print("Switch is OFF")
		else:
			print("Switch is ON")
		time.sleep(0.5)
except KeyboardInterrupt:
	pass # gpiozero cleans up automatically
