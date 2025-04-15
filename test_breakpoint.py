from breakpointSensor import IRSensor

# def test_plastic_sensors():
#     # Creating sensor instances
#     firstIR = IRSensor(26)
#     dropperIR = IRSensor(20)
#     microscopeIR = IRSensor(12)
# 
#     # Checking and printing if an object is detected for each sensor
#     first_detection = firstIR.is_object_detected()
#     print(f"Plastic sensor (26) object detected: {first_detection}")
#     
# 
#     dropper_detection = dropperIR.is_object_detected()
#     print(f"Plastic sensor (20) object detected: {dropper_detection}")
#     
# 
#     microscope_detection = microscopeIR.is_object_detected()
#     print(f"Plastic sensor (12) object detected: {microscope_detection}")
#     assert first_detection == False
#     assert dropper_detection == False
#     assert microscope_detection == False

def test_paper_sensors():
    # Creating sensor instances
    firstIR = IRSensor(23)
    dropperIR = IRSensor(18)
    cameraIR = IRSensor(14)

    # Checking and printing if an object is detected for each sensor
    first_detection = firstIR.is_object_detected()
    print(f"Paper sensor (23) object detected: {first_detection}")

    dropper_detection = dropperIR.is_object_detected()
    print(f"Paper sensor (18) object detected: {dropper_detection}")

    camera_detection = cameraIR.is_object_detected()
    print(f"Paper sensor (14) object detected: {camera_detection}")
    assert first_detection == False
    assert dropper_detection == False
    assert camera_detection == False
    
if __name__=="__main__":
    test_paper_sensors()
