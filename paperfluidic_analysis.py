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
    w = 2300

    cropped_image = image[y:y + h, x:x + w]
    return cropped_image


def paperfluidic_concentration(input_image_path, region_radius=100):
    color_changes = {"Cadmium": 0, "Lead": 0, "Nitrate": 0,
                     "Nitrite": 0, "Phosphate": 0}
    key_list = list(color_changes.keys())
    reservoir_coords = [(1400, 1960), (1950, 1110),
                        (440, 660), (460, 1640), (1380, 340)]

    input_image = crop_image(input_image_path)

    for i, (x, y) in enumerate(reservoir_coords):
        # Extract small regions around the reservoir in both images
        region = input_image[y - region_radius:y + region_radius,
                 x - region_radius:x + region_radius]

        # Compute mean R, G, B values
        mean_r = np.mean(region[:, :, 0])
        mean_g = np.mean(region[:, :, 1])
        mean_b = np.mean(region[:, :, 2])

        color_value = 0.229*mean_r + 0.587*mean_g + 0.114*mean_b

        if i == 0:
            concentration = cadmium_concentration(color_value)
        elif i == 1:
            concentration = lead_concentration(color_value)
        elif i == 2:
            concentration = nitrate_concentration(color_value)
        elif i == 3:
            concentration = nitrite_concentration(color_value)
        else:
            concentration = phosphate_concentration(color_value)

        color_changes[key_list[i]] = concentration

    return color_changes


def cadmium_concentration(imagej):
    if imagej >= 143.9:
        return 0
    elif 130.45 < imagej:
        return (imagej - 144) / -1.35
    elif 119.7 < imagej:
        return (imagej - 132) / -0.119
    elif 106.2 < imagej:
        return (imagej - 123) / -0.0338
    elif 98.4 < imagej:
        return (imagej - 132) / -0.119
    else:
        return (imagej - 103) / (-4.13e-3)


def lead_concentration(imagej):
    if imagej >= 146.6:
        return 0
    elif 135.9 < imagej:
        return (imagej - 147) / -1.07
    elif 133.7 < imagej:
        return (imagej - 136) / -0.0244
    elif 126.8 < imagej:
        return (imagej - 135) / -0.0173
    elif 117.6 < imagej:
        return (imagej - 136) / -0.0184
    else:
        return (imagej - 118) / (-7.43e-4)


def nitrate_concentration(imagej):
    if imagej >= 205.7:
        return 0
    elif 204 < imagej:
        return (imagej - 206) / -0.068
    elif 191.1 < imagej:
        return (imagej - 217) / -0.516
    elif 172.1 < imagej:
        return (imagej - 210) / -0.38
    elif 161 < imagej:
        return (imagej - 175) / -0.0278
    else:
        return (imagej - 173) / -0.0234


def nitrite_concentration(imagej):
    if imagej >= 182.26:
        return 0
    elif 172.13 < imagej:
        return (imagej - 182) / -10.1
    elif 166.68 < imagej:
        return (imagej - 173) / -1.36
    elif 154.78 < imagej:
        return (imagej - 179) / -2.38
    elif 142.57 < imagej:
        return (imagej - 167) / -1.22
    elif 136.19 < imagej:
        return (imagej - 149) / -3.19
    else:
        return (imagej - 147) / -0.273


def phosphate_concentration(imagej):
    if imagej >= 174.09:
        return 0
    elif 171.42 < imagej:
        return (imagej - 174) / -0.0267
    elif 160.98 < imagej:
        return (imagej - 177) / -0.0522
    elif 140.95 < imagej:
        return (imagej - 191) / -0.1
    elif 137.78 < imagej:
        return (imagej - 144) / -(6.34e-3)
    else:
        return (imagej - 141) / (-3.01e-3)
