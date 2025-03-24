from paperfluidic_analysis import paperfluidic_concentration
from microscope_analysis import microplastic_concentration

def test_paperluidic():
    results = paperfluidic_concentration("./test_images/paperfluidic.jpg", "./test_images/paperfluidic_test.jpg")
    #ToDo assert correct values

def test_microplastic():
    result = microplastic_concentration("./test_images/Snap_027.jpg")
    #ToDo assert correct values