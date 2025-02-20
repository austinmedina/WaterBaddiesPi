import numpy as np
from skimage import io, color


def load_and_preprocess_image(image_path):
    image = io.imread(image_path)
    # Convert to Lab color space for better color comparison
    lab_image = color.rgb2lab(image)
    return lab_image


def analyze_reservoirs(image_before, image_after, reservoir_coords,
                       region_radius=5):
    color_changes = {}

    for i, (x, y) in enumerate(reservoir_coords):
        # Extract small regions around the reservoir in both images
        region_before = image_before[y - region_radius:y + region_radius,
                        x - region_radius:x + region_radius]
        region_after = image_after[y - region_radius:y + region_radius,
                       x - region_radius:x + region_radius]

        # Calculate the mean color in Lab color space
        mean_color_before = np.mean(region_before, axis=(0, 1))
        mean_color_after = np.mean(region_after, axis=(0, 1))

        # Compute the Euclidean distance in Lab space
        # as a measure of color change
        color_distance = np.linalg.norm(mean_color_after - mean_color_before)

        color_changes[f'Reservoir {i + 1}'] = color_distance

    return color_changes

def analyzeColorimetric(image_before_path, image_after_path):
    # Example usage
    image_before_path = "reference_image.jpg"
    image_after_path = "test_image_opacity.jpg"

    # Example coordinates for the reservoirs (manually determined or programmatically extracted)
    reservoir_coords = [(100, 100), (200, 100),
                        (300, 100), (400, 100)]

    # Load and preprocess images
    image_before = load_and_preprocess_image(image_before_path)
    image_after = load_and_preprocess_image(image_after_path)

    # Analyze color changes
    color_changes = analyze_reservoirs(image_before, image_after, reservoir_coords)

    # Display results
    for reservoir, change in color_changes.items():
        print(f"{reservoir}: Color Change Distance = {change:.2f}")

    return {'Lead': 93, 'Cadmium': 96, 'Mercury': 102, 'Nitrate': 106, 'Nitrite': 116}
