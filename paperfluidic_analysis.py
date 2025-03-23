import cv2
import numpy as np
from skimage import io, color

def crop_image(image_path):
    image = io.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Apply thresholding to detect the white region (paper)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    # Find contours of the detected regions
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    # Find the largest contour (assuming it is the paper)
    largest_contour = max(contours, key=cv2.contourArea)

    # Get the bounding box of the largest contour
    x, y, w, h = cv2.boundingRect(largest_contour)
    w = 1630

    cropped_image = image[y:y + h, x:x + w]
    return cropped_image

def load_and_preprocess_image(image_path):
    print("Preprocessing Image")
    image = crop_image(image_path)
    # Convert to Lab color space for better color comparison
    lab_image = color.rgb2lab(image)
    return lab_image


def paperfluidic_concentration(reference_image_path, input_image_path,
                               region_radius=5):
    color_changes = {"Mercury": 0, "Lead": 0, "Cadmium": 0,
                     "Nitrate": 0, "Phosphate": 0}
    key_list = list(color_changes.keys())
    reservoir_coords = [(350, 450), (1020, 250),
                        (1410, 800), (1010, 1370), (340, 1170)]

    reference_image = load_and_preprocess_image(reference_image_path)
    input_image = load_and_preprocess_image(input_image_path)
    
    print("Done preprocessing")

    for i, (x, y) in enumerate(reservoir_coords):
        # Extract small regions around the reservoir in both images
        region_before = reference_image[y - region_radius:y + region_radius,
                        x - region_radius:x + region_radius]
        region_after = input_image[y - region_radius:y + region_radius,
                       x - region_radius:x + region_radius]

        # Calculate the mean color
        mean_color_before = np.mean(region_before, axis=(0, 1))
        mean_color_after = np.mean(region_after, axis=(0, 1))

        # Compute the Euclidean distance
        color_distance = np.linalg.norm(mean_color_after - mean_color_before)

        color_changes[key_list[i]] = color_distance
        print(color_distance)

    return color_changes


# image_before_path = "./test_images/paperfluidic.jpg"
# image_after_path = "./test_images/paperfluidic_test.jpg"
# 
# color_changes = paperfluidic_concentration(image_before_path, image_after_path)
# 
# print(color_changes)
# 
# #Display results
# for reservoir, change in color_changes.items():
#     print(f"{reservoir}: Color Change Distance = {change:.2f}")