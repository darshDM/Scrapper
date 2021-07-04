import cv2
import numpy as np
import pytesseract
from PIL import Image
from pytesseract import image_to_string
import os
import time

def get_string(img_path):
    img = cv2.imread(img_path)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, (0, 0, 100), (255, 5, 255))
    # Build mask of non black pixels.
    nzmask = cv2.inRange(hsv, (0, 0, 5), (255, 255, 255))

    # Erode the mask - all pixels around a black pixels should not be masked.
    nzmask = cv2.erode(nzmask, np.ones((3,3)))

    mask = mask & nzmask

    new_img = img.copy()
    new_img[np.where(mask)] = 255
    
    kernel = np.ones((2,2),np.uint8)
    new_img = cv2.erode(new_img, kernel, iterations = 2)
    kernel = np.ones((1,1),np.uint8)
    new_img = cv2.dilate(new_img, kernel, iterations = 1)
    
    cv2.imwrite(img_path,new_img)
    result = pytesseract.image_to_string(Image.open(img_path),config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')

    return result
