import math
import numpy as np
from skimage import io, color, filters, measure, morphology, draw

# Conversion constant determined from testing to get the correct concentration
# due to low amounts of microplastics in each image
# Not using a constant like this would result in a much larger concentration
# than is actually present
conversion_constant = 1/7.34


def crop_image(image_path):
    image = io.imread(image_path)

    # Get image dimensions
    height, width = image.shape[:2]
    radius = min(width, height) // 2  # Make the circle fit within the image
    center = (height // 2, width // 2)  # Center of the image

    # Create a blank mask and draw a filled circle
    mask = np.zeros((height, width), dtype=bool)
    rr, cc = draw.disk(center, radius, shape=mask.shape)
    mask[rr, cc] = True

    # Apply the mask to the image (preserving color channels)
    circular_image = np.zeros_like(image)
    circular_image[mask] = image[mask]

    return circular_image, radius


def microplastic_concentration(image_path):
    image, radius = crop_image(image_path)
    image = color.rgb2gray(image)
    threshold = filters.threshold_yen(image)
    # fig, ax = filters.try_all_threshold(image, figsize=(12,6), verbose=True)

    cleaned_image = morphology.closing(image >= threshold)

    # Label connected regions
    labeled_image = measure.label(cleaned_image, background=0)
    regions = measure.regionprops(labeled_image)

    # Count microplastic particles
    num_particles = len(regions)

    # Volume of each sample (in millimeters)
    volume = 0.075

    # Prevent falsely counting low-signal for particles
    if num_particles >= 10:
        num_particles = 0

    concentration = conversion_constant * num_particles / volume

    print(f'Particles counted: {num_particles} particles')
    print(f'Approximate concentration: {concentration:.2f} particles/mL')

    return concentration
