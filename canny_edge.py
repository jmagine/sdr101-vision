'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Aug 27 2018
                                      TODO

  File Name  : canny_edge.py
  Description: TODO
---*-----------------------------------------------------------------------*'''

import sys
import time
import cv2
import numpy as np

'''[Global vars]------------------------------------------------------------'''
IMAGE_DIR = "/home/jam/projects/forward-vision/images/website"

#color codes for opencv
COLOR_RGB  = 1
COLOR_GRAY = 0
COLOR_ASIS = -1

'''[load_image]----------------------------------------------------------------
  Loads image from given path and returns it
----------------------------------------------------------------------------'''
def load_image(filename, channel_type):
  print()
  print("[load] Loading:\t" + filename.split('/')[-1])

  return cv2.imread(filename, channel_type)

'''[process_image]-------------------------------------------------------------
  TODO
----------------------------------------------------------------------------'''
def process_image(image, filename):
  
  if image is None:
    print("[proc] Image is None")
    sys.exit(1)

  image = cv2.resize(image, (int(image.shape[1] / 2), int(image.shape[0] / 2)), interpolation = cv2.INTER_CUBIC)
  
  image_heq = np.zeros((image.shape[0], image.shape[1], 3), np.uint8)
  
  clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
  for chan in range(3):
    image_heq[:,:,chan] = clahe.apply(image[:,:,chan])
  #image_heq[:,:,0] = cv2.equalizeHist(image[:,:,0])
  #image_heq[:,:,1] = cv2.equalizeHist(image[:,:,1])
  #image_heq[:,:,2] = cv2.equalizeHist(image[:,:,2])
  #image_ycrcb = cv2.cvtColor(image_heq, cv2.COLOR_BGR2YCrCb)
  #image_ycrcb = cv2.bilateralFilter(image_ycrcb, 5, 50, 50)
  #image = cv2.bilateralFilter(image, 5, 50, 50)
  
  #image_heq = cv2.medianBlur(image_heq, 11)
  image_heq = cv2.bilateralFilter(image_heq, 5, 50, 50)
 
  sigma = 0.33
  v = np.median(image[:,:,0])
  lower = int(max(0, (1.0 - sigma) * v))
  upper = int(min(255, (1.0 - sigma) * v))

  upper, image_otsu = cv2.threshold(image_heq[:,:,1], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
  
  image_canny_r = cv2.Canny(image_heq[:,:,0], 0, 100)
  image_canny_g = cv2.Canny(image_heq[:,:,1], 0, 100)
  image_canny_b = cv2.Canny(image_heq[:,:,2], 0, 100)

  image_canny_temp = np.bitwise_and(image_canny_r, image_canny_g)
  image_canny = np.bitwise_and(image_canny_temp, image_canny_b)

  Z = image.reshape((-1, 3))
  Z = np.float32(Z)
  criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
  K = 4
  ret, label, center = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

  center = np.uint8(center)
  res = center[label.flatten()]
  res2 = res.reshape((image.shape))
  cv2.imshow('res2', res2)

  cv2.imshow("Orig", image)
  #cv2.imshow("Heq", image_heq)
  #cv2.imshow("Canny", image_canny)
  
  key = cv2.waitKey(100000)
  if key == ord('s'):
    print("[proc] Saving image")
    cv2.imwrite(filename + "_edges.jpg", res2)

'''[main]----------------------------------------------------------------------
  
----------------------------------------------------------------------------'''
def main():

  filename = IMAGE_DIR + "/" + "DSC04974"
  image = load_image(filename + ".jpg", COLOR_RGB)
  process_image(image, filename)

if __name__ == '__main__':
  main()

