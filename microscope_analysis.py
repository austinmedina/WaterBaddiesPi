import numpy as np
from skimage import io, color, filters, measure, morphology, draw
import os

# Conversion constant determined from testing to get the correct concentration
# due to low amounts of microplastics in each image
# Not using a constant like this would result in a much larger concentration
# than is actually present
conversion_constant = 1/7.34


def crop_image(image_path):
    image = io.imread(image_path)

    # Get image dimensions
    height, width = image.shape[:2]
    radius = min(width, height) // 2.5  # Make the circle fit within the image
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

def save_cropped_image(image_path: str, output_path: str = None) -> str:
    image_path = os.path.normpath(image_path)
    cropped, _ = crop_image(image_path)
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_cropped{ext}"
    io.imsave(output_path, cropped)
    return output_path

if __name__ == "__main__":
    # use a raw string or double backslashes on Windows
    img = r"plasticImages\2025-05-04-21-34-56.790.png"
    new_path = save_cropped_image(img)
    print(f"Saved cropped image to {new_path}")


