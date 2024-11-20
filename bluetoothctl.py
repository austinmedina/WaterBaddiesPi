def run_bluetoothctl(commands):
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
        output, error = process.communicate(input="\n".join(commands) + "\n")
        if error:
            print("Error:", error)
        return output

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    commands_to_run = [
        "power on",
        "agent on",
        "default-agent",
        "scan on",
        # Add more commands as needed
    ]
    result = run_bluetoothctl(commands_to_run)
    print(result) 
