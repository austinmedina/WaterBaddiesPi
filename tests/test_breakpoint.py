from breakpointSensor import IRSensor

def test_plastic_sensors():
    firstIR = IRSensor(26)
    dropperIR = IRSensor(20)
    microscopeIR = IRSensor(12)
    
    assert firstIR.is_object_detected() == False
    assert dropperIR.is_object_detected() == False
    assert microscopeIR.is_object_detected() == False

def test_paper_sensors():
    firstIR = IRSensor(26)
    dropperIR = IRSensor(20)
    cameraIR = IRSensor(12)

    assert firstIR.is_object_detected() == False
    assert dropperIR.is_object_detected() == False
    assert cameraIR.is_object_detected() == False