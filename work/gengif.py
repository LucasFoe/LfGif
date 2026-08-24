# Copyright (c) 2025 Lucas Foerderer
# All rights reserved.

# For inquiries or further information, please contact [Your Email Address].
#
# Used Python packages:
# - numpy
# - imageio
# - PIL
# - opencv

# Note: Replace the placeholders with the actual package names used in your script.

import os
import imageio
import numpy as np
import cv2
from PIL import Image
import logging
import configparser

# Log file path
log_file_path = 'gengif.log'

# Check if log file exists and its size
if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 10 * 1024 * 1024:  # 10MB
    os.remove(log_file_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(file_handler)

# Read duration from gengif.ini
config = configparser.ConfigParser()
config.read('gengif.ini')
duration = config.getint('settings', 'duration', fallback=400)
logger.info("Duration: %d milliseconds", duration)

def align_images(image1, image2):
    gray1 = np.asarray(cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY))
    gray2 = np.asarray(cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY))
    orb = cv2.ORB.create()
    keypoints1, descriptors1 = orb.detectAndCompute(gray1, None)
    keypoints2, descriptors2 = orb.detectAndCompute(gray2, None)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(descriptors1, descriptors2)
    matches = sorted(matches, key=lambda x: x.distance)
    points1 = np.zeros((len(matches), 2), dtype=np.float32)
    points2 = np.zeros((len(matches), 2), dtype=np.float32)
    for i, match in enumerate(matches):
        points1[i, :] = keypoints1[match.queryIdx].pt
        points2[i, :] = keypoints2[match.trainIdx].pt
    h, mask = cv2.findHomography(points2, points1, cv2.RANSAC)
    height, width, channels = image1.shape
    aligned_image = cv2.warpPerspective(image2, h, (width, height))
    return aligned_image

def crop_image(image, crop_box):
    pil_image = Image.fromarray(np.asarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))
    cropped_pil_image = pil_image.crop(crop_box)
    cropped_image = cv2.cvtColor(np.array(cropped_pil_image), cv2.COLOR_RGB2BGR)
    return cropped_image

def find_common_area(images):
    intersection_mask = None

    for image in images:
        gray = np.asarray(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        mask = np.asarray(mask)

        if intersection_mask is None:
            intersection_mask = mask
        else:
            intersection_mask = np.asarray(cv2.bitwise_and(intersection_mask, mask))

    # Ensure the intersection mask is not empty
    if intersection_mask is None or cv2.countNonZero(intersection_mask) == 0:
        raise ValueError("No common area found with image data")

    # Find the bounding box of the intersection mask
    coords = cv2.findNonZero(intersection_mask)
    if coords is None:
        raise ValueError("No common area found with image data")
    x, y, w, h = cv2.boundingRect(np.asarray(coords))
    return (x, y, x + w, y + h)

def generate_gif(jpg_dir='./img', ref_img_dir='./refimg', output_path='./result/output.gif', duration=None):
    if duration is None:
        config = configparser.ConfigParser()
        config.read('gengif.ini')
        duration = config.getint('settings', 'duration', fallback=400)
    logger.info("Duration: %d milliseconds", duration)
    logger.info("Input Directory: %s", os.path.abspath(jpg_dir))
    logger.info("Reference File Directory: %s", os.path.abspath(ref_img_dir))

    images = []
    filelist = sorted([f for f in os.listdir(jpg_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    logger.info("List of input files: %s", filelist)
    if not filelist:
        raise ValueError(f"No image files found in {jpg_dir}")

    middle_file_name = filelist[len(filelist) // 2]

    # Read reference image
    ref_img_files = []
    if ref_img_dir and os.path.exists(ref_img_dir):
        ref_img_files = [f for f in os.listdir(ref_img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if ref_img_files:
        ref_img_path = os.path.join(ref_img_dir, ref_img_files[0])
        imgref = imageio.v2.imread(ref_img_path)
        logger.info("Reference File: %s", os.path.abspath(ref_img_path))
    else:
        imgref = imageio.v2.imread(os.path.join(jpg_dir, middle_file_name))
        logger.info("Reference File: %s", os.path.abspath(os.path.join(jpg_dir, middle_file_name)))

    for file_name in filelist:
        file_path = os.path.join(jpg_dir, file_name)
        img = imageio.v2.imread(file_path)
        imga = align_images(imgref, img)
        images.append(imga)

    # Find the largest common area
    crop_box = find_common_area(images)

    # Crop images to the largest common area
    cropped_images = [crop_image(img, crop_box) for img in images]

    if cropped_images:
        out_dir = os.path.dirname(output_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        imageio.mimsave(output_path, cropped_images, duration=duration)
        logger.info("Output File: %s", os.path.abspath(output_path))
        return output_path
    return None

if __name__ == '__main__':
    generate_gif()
