import matplotlib.pyplot as plt
from skimage import io, color, filters, measure, morphology

def analyzeMicroplastics(imagePath):

    image = io.imread(imagePath)
    #image = io.imread("Snap_038.jpg")
    image = color.rgb2gray(image)
    threshold = filters.threshold_otsu(image)

    cleaned_image = morphology.closing(image >= threshold)

    # Label connected regions
    labeled_image = measure.label(cleaned_image,background=0)
    regions = measure.regionprops(labeled_image)

    # Count microplastic particles
    num_particles = len(regions)

    # Known field of view (in mm²)
    #field_of_view_area = 1#7.5*4  # Adjust based on microscope calibration

    obj_size = 1                     # in mm
    obj_pixels = 62.9
    scale_factor = obj_size / obj_pixels

    # Known field of view (in mm²)
    field_of_view_area = (1280*scale_factor) * (720*scale_factor)
    # field_of_view_area = 15*19
    depth = 1        # in mm
    volume = field_of_view_area * depth / 1000

    print(field_of_view_area)

    concentration = num_particles / volume

    print(f'Approximate concentration: {concentration:.2f} particles/mL')
    return {"microplastics":concentration}

    # # Display
    # fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    # ax[0].imshow(image)
    # ax[0].axis("off")

    # ax[1].imshow(labeled_image)
    # ax[1].axis("off")

    # plt.tight_layout()
    # plt.show()
