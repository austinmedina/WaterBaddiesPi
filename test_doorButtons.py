from gpiozero import LED, Button
import time

button = Button(4)
#button = Button(15)
#led1 = LED(8)
led2 = LED(19)
try:
	while True:
		if button.is_pressed:
			print("Switch is OFF")
			#led1.off()
			led2.off()
		else:
			print("Switch is ON")
			#led1.on()
			led2.on()
		time.sleep(0.5)
except KeyboardInterrupt:
	pass # gpiozero cleans up automatically
