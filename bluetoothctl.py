import subprocess

def useBluetoothCtl(commands):
	"""
	Run a series of commands in bluetoothctl.
	:param commands: List of commands to send to bluetoothctl
	:return: Output from bluetoothctl
	"""
	try:
		# Open a bluetoothctl process
		process = subprocess.Popen(
			["bluetoothctl"],
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True
		)

		# Send commands to bluetoothctl
		for command in commands:
			# Write command to stdin and flush to ensure it is sent
			process.stdin.write(command + '\n')
			process.stdin.flush()

		# Now collect the output and error messages from the process
		output, error = process.communicate()

		if error:
			print("Error:", error)
		return output

	except Exception as e:
		print(f"An error occurred: {e}")
		return None

if __name__ == "__main__":
	# Example usage
	commands_to_run = [
		"help",
		"power on",
		"menu advertise", 
		"manufacturer 0x1000",
		"name on",
		'name "BaddiesDetectionSystem"',
		"back",
		"system-alias BaddiesDetectionSystem",
		"menu gatt",
		"register-service 0x1100",
		"yes",
		"register-characteristic 0x1110 Flags=read,notify",
		"62 61 64 64 69 65 73",
		"register-application",
		"back",
		"advertise on",
		"discoverable on",
		# Add more commands as needed
	]
	result = useBluetoothCtl(commands_to_run)
	print(result)
