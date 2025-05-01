from breakpointSensor import IRSensor


def test_plastic_sensors():
    # Creating sensor instances
    firstIR = IRSensor(12)
    dropperIR = IRSensor(26)
    microscopeIR = IRSensor(20)

    # Checking and printing if an object is detected for each sensor
    first_detection = firstIR.is_object_detected()
    print(f"Plastic sensor (12) object detected: {first_detection}")
    

    dropper_detection = dropperIR.is_object_detected()
    print(f"Plastic sensor (26) object detected: {dropper_detection}")
    

    microscope_detection = microscopeIR.is_object_detected()
    print(f"Plastic sensor (20) object detected: {microscope_detection}")
    assert first_detection == False
    assert dropper_detection == False
    assert microscope_detection == False

def test_paper_sensors():
    # Creating sensor instances
    firstIR = IRSensor(14)
    dropperIR = IRSensor(18)
    cameraIR = IRSensor(23)

    # Checking and printing if an object is detected for each sensor
    first_detection = firstIR.is_object_detected()
    print(f"Paper sensor (14) object detected: {first_detection}")

    dropper_detection = dropperIR.is_object_detected()
    print(f"Paper sensor (18) object detected: {dropper_detection}")

    camera_detection = cameraIR.is_object_detected()
    print(f"Paper sensor (23) object detected: {camera_detection}")
    assert first_detection == False
    assert dropper_detection == False
    assert camera_detection == False
    
def test_dropperBreak_sensors():
    # Creating sensor instances
    dropperBreak1 = IRSensor(0)
    dropperBreak2 = IRSensor(1)

    # Checking and printing if an object is detected for each sensor
    dropperBreak1_detection = dropperBreak1.is_object_detected()
    print(f"dropperBreak1 (0) object detected: {dropperBreak1_detection}")
    

    dropperBreak2_detection = dropperBreak2.is_object_detected()
    print(f"dropperBreak2 (1) object detected: {dropperBreak2_detection}")
    
    assert dropperBreak1_detection == False
    assert dropperBreak2_detection == False
    
if __name__=="__main__":
    test_paper_sensors()
    test_plastic_sensors()
    test_dropperBreak_sensors()
