'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Aug 15 2018
                                 forward-vision

  File Name  : forward_vision.py
  Description: Main application for forward vision, looks for targets as
               specified by master module or manually specified. Can be placed
               in live mode for use with real robot, loopback mode to play back
               footage from mission and publish to DSM, or read mode to just
               run algorithms on previous missions
---*-----------------------------------------------------------------------*'''

import utils

import os
import sys
import time

import cv2
import numpy as np

'''[Global vars]------------------------------------------------------------'''

#MODE_LIVE
# - takes pics and processes them in real time
# - also saves pics before processing for later playback
# - publishes predicted target locations to DSM
#   - these targets range from y=[-1,1], z=[-1,1] and represent the approximate
#     section that targets are in within the image
MODE_LIVE = 0

#MODE_READ
# - plays back a stream of images through processing function
# - this does not get published to DSM and is not intended to interface with
#   other robot modules
MODE_READ = 1

#MODE_LOOP
# - loop a playback stream into DSM
MODE_LOOP = 2

#current mode in use
MODE = MODE_READ

DISPLAY_IMAGES = True
PRINT_TIMING = True

#color codes for opencv
COLOR_RGB  = 1
COLOR_GRAY = 0
COLOR_ASIS = -1

#image shapes (width, height) for use with opencv
HIGH_RES = (960, 720)
MID_RES  = (640, 480)
LOW_RES  = (320, 240)

#meanshiftfilter spatial radius and color radius
MSF_SPATIAL = 15
MSF_COLOR = 25

#houghes line detection minimum line length and maximum line gap
#MIN_LINE_LEN = 25
#MAX_LINE_GAP = 2
MIN_LINE_LEN = 25
MAX_LINE_GAP = 2

#location to save images in live mode
IMAGES_DIR = "/home/jam/projects/forward-vision/images/dev/"
READ_POS = 662

#input image shape (width, height)
IMAGE_SHAPE = HIGH_RES

#time between images in seconds
MIN_IMAGE_INTERVAL = 1.0

#DSM variables for live mode
DSM_serverID = 45
DSM_clientID = 100

'''[kmeans]--------------------------------------------------------------------
  Segments image into K colors by finding closest groups for each pixel
----------------------------------------------------------------------------'''
def kmeans(image):
  Z = image.reshape((-1, 3))
  Z = np.float32(Z)
  criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
  K = 16
  ret, label, center = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
  center = np.uint8(center)
  res = center[label.flatten()]
  return res.reshape((image.shape))

'''[process_image]-------------------------------------------------------------
  Function to handle processing of image

  image - input image array
  
  max_x - most confident x coordinate
  max_y - most confident y coordinate
  confidence - confidence in range [0,255] for detection
----------------------------------------------------------------------------'''
def process_image(image):
  
  global READ_POS
  
  #[sanity checks]-------------------------------------------------------------
  if image is None:
    print("[proc] Image is None")
    sys.exit(1)
  
  #[preprocessing]-------------------------------------------------------------
  start = time.time()
  
  #resize images to low or mid res for faster processing
  #image = cv2.resize(image, LOW_RES, interpolation = cv2.INTER_CUBIC)
  
  image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
  image_hsv = cv2.bilateralFilter(image_hsv, 5, 50, 50)

  #image_ycrcb = cv2.cvtColor(image_heq, cv2.COLOR_BGR2YCrCb)
  #image_ycrcb = cv2.bilateralFilter(image_ycrcb, 5, 50, 50)
  
  end = time.time()

  if PRINT_TIMING:
    print("[proc] Preproc:\t%.5f" % (end - start))

  #[binary red]----------------------------------------------------------------
  start = time.time()
  
  red_lower = np.array([0, 0, 0], np.uint8)
  red_upper = np.array([30, 255, 255], np.uint8)
  red_binary_1 = cv2.inRange(image_hsv, red_lower, red_upper)
  
  red_lower = np.array([150, 0, 0], np.uint8)
  red_upper = np.array([180, 255, 255], np.uint8)
  red_binary_2 = cv2.inRange(image_hsv, red_lower, red_upper)
  
  red_binary = cv2.bitwise_or(red_binary_1, red_binary_2)
  
  end = time.time()

  if PRINT_TIMING:
    print("[proc] Bin red:\t%.5f" % (end - start))

  #[hist backprojection]-------------------------------------------------------
  start = time.time()
  
  image_hist = cv2.calcHist([image_hsv], [0, 1], None, [180, 255], [0, 30, 0, 255])
  cv2.normalize(image_hist, image_hist, 0, 255, cv2.NORM_MINMAX)
  dest_1 = cv2.calcBackProject([image_hsv], [0, 1], image_hist, [0, 30, 0, 255],1)
  
  disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
  cv2.filter2D(dest_1, -1, disc, dest_1)
  ret, thresh = cv2.threshold(dest_1, 128, 255, 0)
  thresh = cv2.merge((thresh, thresh, thresh))
  dest_1 = cv2.bitwise_and(image_hsv, thresh)
  
  image_hist = cv2.calcHist([image_hsv], [0, 1], None, [180, 255], [150, 180, 0, 255])
  cv2.normalize(image_hist, image_hist, 0, 255, cv2.NORM_MINMAX)
  dest_2 = cv2.calcBackProject([image_hsv], [0, 1], image_hist, [150, 180, 0, 255],1)

  disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
  cv2.filter2D(dest_2, -1, disc, dest_2)
  ret, thresh = cv2.threshold(dest_2, 128, 255, 0)
  thresh = cv2.merge((thresh, thresh, thresh))
  dest_2 = cv2.bitwise_and(image_hsv, thresh)

  dest = cv2.bitwise_or(dest_1, dest_2)

  end = time.time()

  if PRINT_TIMING:
    print("[proc] Hist BP:\t%.5f" % (end - start))

  #[hist equalization]---------------------------------------------------------
  start = time.time()
  
  #image = cv2.bilateralFilter(image, 5, 50, 50)
  image_heq = np.zeros((image.shape[0], image.shape[1], 3), np.uint8)
  
  clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
  for chan in range(3):
    image_heq[:,:,chan] = clahe.apply(image[:,:,chan])
    #image_heq[:,:,chan] = cv2.equalizeHist(image[:,:,chan])
  
  image_heq = cv2.bilateralFilter(image_heq, 5, 50, 50)

  end = time.time()

  if PRINT_TIMING:
    print("[proc] Hist EQ:\t%.5f" % (end - start))

  #[kmeans segmentation]-------------------------------------------------------
  #res2 = kmeans(image_heq)

  #[canny]---------------------------------------------------------------------
  start = time.time()
  
  sigma = 0.33
  #v = np.median(image_ycrcb[:,:,2])
  v = np.median(image_heq[:,:,2])
  lower = int(max(0, (1.0 - sigma) * v))
  upper = int(min(255, (1.0 + sigma) * v))
  
  #on image_ycrcb
  #upper, image_otsu = cv2.threshold(image_ycrcb[:,:,2], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
  #image_canny = cv2.Canny(image_ycrcb[:,:,2], 0, upper / 2)
  
  #on image_heq
  upper, image_otsu = cv2.threshold(image_heq[:,:,2], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
  image_canny = cv2.Canny(image_heq[:,:,2], 0, upper / 2)

  #image_canny = cv2.morphologyEx(image_canny, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8))
  
  print("[proc] Canny lower/upper: " + str(lower) + " " + str(upper))

  end = time.time()

  if PRINT_TIMING:
    print("[proc] Canny:\t%.5f" % (end - start))

  #[hough lines]---------------------------------------------------------------
  start = time.time()

  houghlines = np.zeros(red_binary.shape, np.uint8)
  lines = cv2.HoughLinesP(red_binary, 1, np.pi/180, 100, MIN_LINE_LEN, MAX_LINE_GAP)
  if lines is not None:
    for line in lines:
      for x1, y1, x2, y2 in line:
        cv2.line(houghlines, (x1, y1), (x2, y2), 255, 1)
        #cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 1)
  #houghlines = cv2.dilate(houghlines, kernel, iterations = 1)

  end = time.time()

  if PRINT_TIMING:
    print("[proc] Hough:\t%.5f" % (end - start))

  #[adaptive thresholding]-----------------------------------------------------
  '''
  image_adaptive = cv2.adaptiveThreshold(image[:,:,1], 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 5)
  
  #perform morphological operations on adaptive image
  #kernel = np.ones((5,5), np.uint8)  
  #image_adaptive = cv2.morphologyEx(image_adaptive, cv2.MORPH_OPEN, kernel)
  
  kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
  image_adaptive = cv2.erode(image_adaptive, kernel)
  image_adaptive = cv2.dilate(image_adaptive, kernel, iterations = 0)
  '''

  #[contours]------------------------------------------------------------------
  _, contours, hierarchy = cv2.findContours(red_binary.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
  
  print("[proc] Num contours: " + str(len(contours)))
  image = cv2.drawContours(image, contours, -1, (0, 255, 0), 2)

  #TODO could do things with individual contours
  #all_contours = [{'i': i, 'contour': contours[i]} for i in range(len(contours))]
  #for contour in all_contours:
  #  cv2.drawContour(contour, 

  if DISPLAY_IMAGES:
    images = []
    
    images.append(image)
    images.append(image_hsv[:,:,0])
    images.append(image_hsv[:,:,2])
    
    images.append(red_binary)
    images.append(dest)
    images.append(image_heq[:,:,0])
    
    images.append(image_heq[:,:,2])
    images.append(image_canny)
    images.append(houghlines)
    
    #images.append(res2)
    #images.append(image_ycrcb)
    #images.append(image_ycrcb[:,:,2])
    #images.append(image_otsu)

    utils.display_stacked(images, LOW_RES, 3, 3)
  
    #do not wait for input, but wait enough to display images
    # also holding q will usually allow the pi to quit
    if MODE == MODE_LIVE:
      key = cv2.waitKey(50)
      if key == ord('q'):
        print("[proc] Detected q, exiting")
        sys.exit(0)

    #wait for input from user, use space or arrow keys to advance/nav stream
    else:
      key = ''
      while True:
        key = cv2.waitKey(100000)
        if key == ord('q'):
          print("[proc] Detected q, exiting")
          sys.exit(0)

        #left
        elif key == ord('a'):
          READ_POS -= 1
          break
        #right
        elif key == ord('d') or key == ord(' '):
          READ_POS += 1
          break

  #return max_x, max_y, int(max_count * 255 / total_count)
  return 0, 0, 0


'''[main]----------------------------------------------------------------------
  Main driver, creates file structure for images, handles existing/non-existing
  directories, and feeds images into process_image() for target detection.

  In live mode, this reads images from a Pi camera, writes them to a file, 
  processes the images, and publishes results to DSM buffer. It is also capable
  of displaying images, but will not wait for user input. Images are taken in
  either after an interval or as soon as the processing is done, whichever is
  later.

  In read mode, this feeds images in from a directory, processes the images,
  and displays the results while waiting for user input to continue or quit
----------------------------------------------------------------------------'''
def main():
  
  global READ_POS

  #only init dsm client and buffers if necessary
  if MODE == MODE_LIVE or MODE == MODE_LOOP:
    print("[info] Initializing DSM client")
    client = pydsm.Client(DSM_serverID, DSM_clientID, True)

    print("[info] Initializing local buffers")
    client.registerLocalBuffer(TARGET_LOCATION, sizeof(Location), False)
  
  #handle directory creation for saving images
  # - IMAGES_DIR should already exist, but create one if not there
  # - IMAGES_DIR_SUBDIR should not exist, but if it does, start adding (0), (1), etc to tail
  if MODE == MODE_LIVE:
    
    IMAGES_DIR_FULL = utils.gen_timestamp_dir(IMAGES_DIR)
    print("[main] All images being saved to: " + IMAGES_DIR_FULL)
    
    #open camera and set capture parameters
    with PiCamera() as camera:
      camera.resolution = IMAGE_SHAPE
      camera.framerate = 32
      rawCapture = PiRGBArray(camera, size=IMAGE_SHAPE)

      time.sleep(0.5)

      print("[main] Capture starting")

      last_time = time.time()
      image_count = 0
      
      #start camera stream
      for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        #attempt to terminate more smoothly on keyboard interrupts
        try:
          curr_time = time.time()
          if curr_time - last_time < MIN_IMAGE_INTERVAL:
            rawCapture.truncate(0)
            continue
          
          #print heartbeat to terminal every 10 images
          if image_count % 10 == 0:
            print("[main] Image count: " + str(image_count) + " Interval: " + str(curr_time - last_time) + " ImgDir: " + IMAGES_DIR_FULL.split("/")[-2])

          last_time = time.time()

          cv2.imwrite(IMAGES_DIR_FULL + str(image_count) + '.jpg', frame.array)
          rawCapture.truncate(0)
          image_count += 1

          x, y, confidence = process_image(frame.array)
          #x,y,z,confidence = process_image(frame.array)

          #pack and publish results to DSM buffer
          utils.pub_loc(client, 0, x, y, confidence, image_count % 256)
          
          ''' #DEBUG publishes all x/y/z values, used for testing downstream programs
          for x in range(-1, 2):
            for y in range(-1, 2):
              for z in range(-1, 2):
                l = Location()
                l.x = x
                l.y = y
                l.z = z
                l.confidence = confidence

                buf = Pack(l)
                client.setLocalBufferContents(TARGET_LOCATION, buf)
                print(x, y, z, confidence)
                time.sleep(5)
          '''
        except KeyboardInterrupt:
          print("[main] Ctrl + C detected. Breaking stream")
          break
        except Exception as e:
          print("[main] [error]: " + str(e))
          break
  
  #READ_MODE
  elif MODE == MODE_READ:
    IMAGES_SUBDIR = "10_41_30"

    #generate list of all image names
    image_list = os.listdir("/home/jam/projects/forward-vision/images/comp/" + IMAGES_SUBDIR)
    image_list.sort(key = lambda x: int(x.split(".")[0]))
    
    #such turing machine
    while READ_POS >= 0 and READ_POS < len(image_list):
      image = utils.load_image("/home/jam/projects/forward-vision/images/comp/" + IMAGES_SUBDIR + "/" + str(image_list[READ_POS]), COLOR_RGB)
      process_image(image)

      if READ_POS < 0 or READ_POS >= len(image_list):
        print("[main] Exit? y/n")

        while True:
          key = cv2.waitKey(100000)

          if key == ord('q') or key == ord('y'):
            sys.exit(0)
          elif key == ord('n'):
            if READ_POS < 0:
              READ_POS = len(image_list) - 1
            else:
              READ_POS = 0
            break

  else:
    IMAGES_SUBDIR = "comp/buoys_1"
    
    image_count = 0
    for i in range(1584, 1687):
      image = utils.load_image("/home/jam/projects/forward-vision/images/" + IMAGES_SUBDIR + "/" + str(i) + ".jpg", COLOR_RGB)
      x, y, confidence = process_image(image)
      image_count += 1
      #pack and publish results to DSM buffer
      utils.pub_loc(client, 0, x, y, confidence, image_count % 256)

#conditional imports which require integration with rest of system
if MODE == MODE_LIVE or MODE == MODE_LOOP:

  sys.path.append("/home/pi/DistributedSharedMemory/")
  sys.path.append("/home/pi/PythonSharedBuffers/src/")

  import pydsm
  from Constants import *
  from Vision import Location
  from Serialization import *
  from ctypes import sizeof
  from Master import *
  from picamera.array import PiRGBArray
  from picamera import PiCamera

if __name__ == '__main__':
  main()

