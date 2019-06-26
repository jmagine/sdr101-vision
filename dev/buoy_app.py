'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Aug 01 2018
                                    forwardvision

  File Name  : buoy_app.py
  Description: Application to look for targets in predefined sections of the
               image. Can be placed in either live mode for use with real robot
               or placed in read mode to playback footage from a live mission.
---*-----------------------------------------------------------------------*'''

import os
import sys
import time
import datetime

import cv2
import numpy as np

now = datetime.datetime.now()
print("Current time is: " + str(now))

now = str(now).split(".")[0]
now = now.replace(" ", "/")
now = now.replace(":", "_")

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

#input image shape (width, height)
IMAGE_SHAPE = HIGH_RES

#time between images in seconds
MIN_IMAGE_INTERVAL = 1.0

#DSM variables for live mode
DSM_serverID = 45
DSM_clientID = 100

#IMAGES_SUBDIR = "08-01-18_entire_run_1"
#IMAGES_SUBDIR = "08-01-18_buoys"

'''[pub_loc]-------------------------------------------------------------------
  Publishes location to DSM buffer
----------------------------------------------------------------------------'''
def pub_loc(client, x, y, z, conf, loctype):
  l = Location()
  l.x = x
  l.y = y
  l.z = z
  l.confidence = conf
  l.loctype = loctype
  client.setLocalBufferContents(TARGET_LOCATION, Pack(l))
  print("[main] [dsm] publishing x:" + str(l.x) + " y:" + str(l.y) + " z:" + str(l.z) + " id:" + str(l.loctype) + " c:" + str(l.confidence))
          
'''[load_image]----------------------------------------------------------------
  Loads image from given path and returns it
----------------------------------------------------------------------------'''
def load_image(filename, channel_type):
  print()
  print("[load] Loading:\t" + filename.split('/')[-1])

  return cv2.imread(filename, channel_type)

'''[cc]------------------------------------------------------------------------
  Connected components algorithm, dilates and masks using original image to
  label all CCs in image
----------------------------------------------------------------------------'''
def cc(image):
  # Find all connected components
  start = time.time()
  image_cc_all = np.zeros((image.shape), np.uint8)

  label_count = 1
  image_cc = np.zeros((image.shape), np.uint8)
  image_cc_old = np.zeros((image.shape), np.uint8)

  kernel = np.ones((5,5), np.uint8)

  for y in range(len(image)):
    for x in range(len(image[0])):
      if(image[y][x] > 0 and image_cc_all[y][x] == 0):
        image_cc = image_cc & 0
        image_cc_old = image_cc_old & 0
        #print(image_cc.max(), image_cc.min(), image_cc_old.max(), image_cc_old.min())
        image_cc[y][x] = 1

        # fill in the entire connected component using dilation and masking
        while not np.array_equal(image_cc, image_cc_old):
          image_cc_old = image_cc
          image_cc = cv2.dilate(image_cc, kernel, iterations = 1) & image
        
        image_cc_all += image_cc * label_count
        label_count += 1
  end = time.time()
  if PRINT_TIMING:
    print("[proc] [time] CC:\t%.5f" % (end - start))

  # check if there are enough connected components
  if label_count == 1:
    print("[proc] No CCs found")
    return [], image_cc_all

  # find centers of connected components
  labels_x = [0 for x in range(label_count)]
  labels_y = [0 for x in range(label_count)]
  labels_counts = [0 for x in range(label_count)]

  for y in range(len(image)):
    for x in range(len(image[0])):
      if(image_cc_all[y][x] > 0):
        labels_x[image_cc_all[y][x]] += x
        labels_y[image_cc_all[y][x]] += y
        labels_counts[image_cc_all[y][x]] += 1
  
  labels = []
  for i in range(len(labels_counts)):
    if labels_counts[i] != 0:
      labels.append((int(labels_x[i] / labels_counts[i]), int(labels_y[i] / labels_counts[i]), 5))
  
  image_cc_all = cv2.normalize(image_cc_all, None, 0, 255, cv2.NORM_MINMAX)
  
  print(labels_x)
  print(labels_y)
  print(labels_counts)

  return labels, image_cc_all

'''[section_max_binary]--------------------------------------------------------
  Finds section of image with most detections in it and returns the coordinates
  of that section as well as metrics that can be used to estimate confidence
  
  [image      ] - image to section and find max detections on
  [part_height] - number of partitions in y-axis
  [part_width ]- number of partitions in x-axis

  [max_x] - maximum x coordinate of section
  [max_y] - maximum y coordinate of section
  [max_count  ] - count of pixels detected in max section
  [total_count] - count of all detected pixels
----------------------------------------------------------------------------'''
def section_max_binary(image, part_height=3, part_width=3):
  #part_height = 3
  #part_width = 3

  sect_height = int(image.shape[0] / part_height)
  sect_width = int(image.shape[1] / part_width)

  #image_sects = np.zeros((part_height, part_width, np.)
  
  sub_image = np.zeros((sect_height, sect_width), np.uint8)
  sub_image_counts = np.zeros((part_height, part_width), np.uint32)
  
  for part_y in range(part_height):
    for part_x in range(part_width):
      sub_image = image[part_y * sect_height : (part_y + 1) * sect_height, part_x * sect_width : (part_x + 1) * sect_width]
      
      count = int(np.sum(sub_image) / 255)
      '''
      count = 0
      for y in range(sect_height):
        for x in range(sect_width):
          if sub_image[y][x] > 0:
            count += 1
            #sub_images[part_y][part_x][y][x] = 128
      '''

      sub_image_counts[part_y][part_x] = count

  #print("[proc] Sect counts: ")
  #print(sub_image_counts)
  
  max_count = 0
  max_x = int(part_width / 2)
  max_y = int(part_height / 2)
  total_count = 0
  for part_y in range(part_height):
    for part_x in range(part_width):
      if sub_image_counts[part_y][part_x] > max_count:
        max_count = sub_image_counts[part_y][part_x]
        max_x = part_x
        max_y = part_y
      total_count += sub_image_counts[part_y][part_x]

  #draw section dividing lines on original image
  for x in range(part_width):
    cv2.line(image, (sect_width * x, 0), (sect_width * x, image.shape[0]), 128, 1)
  
  for y in range(part_height):
    cv2.line(image, (0, sect_height * y), (image.shape[1], sect_height * y), 128, 1)
  
  #fill in the current max_sect
  for y in range(sect_height):
    for x in range(sect_width):
      if image[max_y * sect_height + y][max_x * sect_width + x] == 0:
        image[max_y * sect_height + y][max_x * sect_width + x] = 64
  
  #print(max_x, max_y, max_count, total_count)
  return max_x, max_y, max_count, total_count

'''[process_image]-------------------------------------------------------------
  Function to handle processing of image

  image - input image array
  
  max_x - most confident x coordinate
  max_y - most confident y coordinate
  confidence - confidence in range [0,255] for detection
----------------------------------------------------------------------------'''
def process_image(image):
  
  if image is None:
    print("[proc] Image is None")
    sys.exit(1)
  
  #apply preprocessing to base image
  start = time.time()
  
  #resize images to low or mid res for faster processing
  image = cv2.resize(image, LOW_RES, interpolation = cv2.INTER_CUBIC)
  image = cv2.bilateralFilter(image, 5, 50, 50)
  #image = cv2.bilateralFilter(image, 5, 50, 50)

  #create canny image
  #image_canny = cv2.Canny(image[:,:,2], 0, 150)
  
  #create adaptive thresholded image on green channel
  image_adaptive = cv2.adaptiveThreshold(image[:,:,1], 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 5)
  
  #perform morphological operations on adaptive image
  #kernel = np.ones((5,5), np.uint8)  
  #image_adaptive = cv2.morphologyEx(image_adaptive, cv2.MORPH_OPEN, kernel)
  
  kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
  image_adaptive = cv2.erode(image_adaptive, kernel)
  image_adaptive = cv2.dilate(image_adaptive, kernel, iterations = 0)
  
  #find contours of adaptivethresholding image
  #_, contours, hierarchy = cv2.findContours(image_adaptive.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
  
  #print("[main] Num contours: " + str(len(contours)))
  #image = cv2.drawContours(image, contours, 1, (0, 255, 0), 2)

  #all_contours = [{'i': i, 'contour': contours[i]} for i in range(len(contours))]
  
  #for contour in all_contours:
  #  cv2.drawContour(contour, 

  end = time.time()
  
  if PRINT_TIMING:
    print("[proc] Preproc:\t%.5f" % (end - start))
  
  #use connected components to filter out small objects
  start = time.time()
  nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(image_adaptive, connectivity=8)
  
  #take out the background, which is considered a component
  sizes = stats[1:, -1]; nb_components = nb_components - 1

  #min size of particle
  min_size = 100

  for i in range(nb_components):
    if sizes[i] < min_size:
      image_adaptive[output == i + 1] = 0
  
  end = time.time()
  
  if PRINT_TIMING:
    print("[proc] CC:\t%.5f" % (end - start))

  '''
  _, contours, _ = cv2.findContours(image_can_r.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
  contours = sorted(contours, key = cv2.contourArea, reverse = True)[:10]
  
  for c in contours:
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * peri, True)

    cv2.drawContours(image, [approx], -1, (0, 255, 0), 3)
  '''

  '''
  #compute hough lines and add to houghlines  
  start = time.time()
  houghlines = np.zeros(image_adaptive.shape, np.uint8)

  lines = cv2.HoughLinesP(image_adaptive, 1, np.pi/180, 100, MIN_LINE_LEN, MAX_LINE_GAP)
  if lines is not None:
    for line in lines:
      for x1, y1, x2, y2 in line:
        cv2.line(houghlines, (x1, y1), (x2, y2), 255, 1)
        cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 1)
  houghlines = cv2.dilate(houghlines, kernel, iterations = 1)
  end = time.time()
  print("[proc] Hough:\t" + str(end - start))
  '''

  start = time.time()
  max_x, max_y, max_count, total_count = section_max_binary(image_adaptive, 5, 5)
  
  if max_count == 0:
    print("[smax] No targets found.")
    total_count = 1
    
    #maintain straight heading
    max_x = 0
    max_y = 0
  else:
    max_x -= 2
    max_y -= 2

  end = time.time()
  
  if PRINT_TIMING:
    print("[proc] Sec Max:\t%.5f" % (end - start))
  
  if MODE == MODE_READ:
    print("[proc] Max sec: [x:" + str(max_x) + " y:" + str(max_y) + "]")
  
  '''
  circles = cv2.HoughCircles(image_adaptive, cv2.HOUGH_GRADIENT, 4, 1, param1=100, param2=100, minRadius=0, maxRadius=0)
  
  if circles is not None:
    circles = np.uint16(np.around(circles))
    for i in circles[0,:]:
      # draw the outer circle
      #cv2.circle(image,(i[0],i[1]),i[2],(0,255,255),2)
      # draw the center of the circle
      #cv2.circle(image,(i[0],i[1]),2,(0,0,255),3)
      print(i[0], i[1])
  else:
    print("[proc] No circles found")
  '''

  #do connected components
  '''
  labels, image_cc_all = cc(houghlines)

  if len(labels) == 0:
    print("[proc] No labels found")
    pass
  else:
    print("[proc] Labels: " + str(len(labels)))
    # find an appropriate target using these labels
    i = int(len(labels) / 4)
    target_quarter = labels[i]
  '''

  
  #print(sub_images)
  #perform any scaling before displaying and saving
  #image = cv2.resize(image, LOW_RES, interpolation = cv2.INTER_CUBIC)
  #image_can = cv2.resize(image_can, HIGH_RES, interpolation = cv2.INTER_CUBIC)
  #image_can_overlay = cv2.resize(image_can_overlay, HIGH_RES, interpolation = cv2.INTER_CUBIC)
  #print(image_can.max(), image_can.min())
  
  #for i in range(len(labels)):
  #  labels[i] = tuple(x * 3 for x in labels[i])
  
  #for i in range(len(labels)):
  #  if labels[i] == target_quarter:
  #    cv2.circle(image, (labels[i][0], labels[i][1]), labels[i][2], (0,255,255), -1)
  #  else:
  #    cv2.circle(image, (labels[i][0], labels[i][1]), labels[i][2], (0,0,255), -1)
  
  #cv2.circle(image, target_mean, 5, (0, 255, 0))
  #print("[proc] Num CC: " + str(label_count))
  
    
  if DISPLAY_IMAGES:
    cv2.imshow("Image", image)
    cv2.imshow("Image Adaptive", image_adaptive)
    #cv2.imshow("Connected Components", image_cc_all)
    #cv2.imshow("Houghlines", houghlines)
    #cv2.imshow("Canny", image_canny)
    '''
    for y in range(part_height):
      for x in range(part_width):
        cv2.imshow("Houghlines [" + str(y) + " " + str(x) + "]", sub_images[y][x])
    '''
    #cv2.imshow("Red", image[:,:,2])
    #cv2.imshow("Green", image[:,:,1])
    #cv2.imshow("Blue", image[:,:,0])
  
    #do not wait for input, but wait enough to display images
    # also holding q will usually allow the pi to quit

    if MODE == MODE_LIVE:
      key = cv2.waitKey(50)
      if key == ord('q'):
        print("[proc] Detected q, exiting")
        sys.exit(0)
    #wait for input from user, use space to advance stream
    else:
      key = ''
      while key != ord(' '):
        key = cv2.waitKey(100000)

        if key ==  ord('q'):
          print("[proc] Detected q, exiting")
          sys.exit(0)

  return max_x, max_y, int(max_count * 255 / total_count)

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
  
  if MODE == MODE_LIVE or MODE == MODE_LOOP:
    #initialize dsm client and buffers
    print("[info] Initializing DSM client")
    client = pydsm.Client(DSM_serverID, DSM_clientID, True)

    print("[info] Initializing local buffers")
    client.registerLocalBuffer(TARGET_LOCATION, sizeof(Location), False)

  if MODE == MODE_LIVE:
    #handle directory creation for all images for current run
    # - IMAGES_DIR should already exist, but create one if not there
    # - IMAGES_DIR_SUBDIR should not exist, but if it does, start adding (0), (1), etc to tail
    print("[main] Checking for general directory at: " + IMAGES_DIR)
    
    #DEBUG set now to hardcode image subdir
    #now = "TEST"

    if not os.path.exists(IMAGES_DIR):
      print("[main] Creating directory at: " + IMAGES_DIR)
      os.makedirs(IMAGES_DIR)

    IMAGES_DIR_SUBDIR = IMAGES_DIR + now
    if not os.path.exists(IMAGES_DIR_SUBDIR):
      print("[main] Creating directory at: " + IMAGES_DIR_SUBDIR)
      os.makedirs(IMAGES_DIR_SUBDIR)
      IMAGES_DIR_FULL = IMAGES_DIR_SUBDIR + "/"
    else:
      print("[main] Directory already exists. Creating at next available")
      i = 0
      IMAGES_DIR_SUBDIR_TAIL = IMAGES_DIR_SUBDIR + "-" + str(i) + "/"
      while True:
        if not os.path.exists(IMAGES_DIR_SUBDIR_TAIL):
          print("[main] Found spot. Creating directory at: " + IMAGES_DIR_SUBDIR_TAIL)
          os.makedirs(IMAGES_DIR_SUBDIR_TAIL)
          IMAGES_DIR_FULL = IMAGES_DIR_SUBDIR_TAIL
          break
        i += 1
        IMAGES_DIR_SUBDIR_TAIL = IMAGES_DIR_SUBDIR + "-" + str(i) + "/"

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
          pub_loc(client, 0, x, y, confidence, image_count % 256)
          #l = Location()
          #l.x = 0
          #l.y = x
          #l.z = y
          #l.confidence = confidence
          #l.loctype = image_count % 256

          #buf = Pack(l)
          #client.setLocalBufferContents(TARGET_LOCATION, buf)
          #print("[main] [dsm] publishing x: " + str(l.x) + " y: " + str(l.y) + " z: " + str(l.z) + "id: " + str(l.loctype) + " c: " + str(l.confidence))
          
          ''' #DEBUG iterates over all x/y/z values
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
    for i in range(461, 1268):
      image = load_image("/home/jam/projects/forward-vision/images/comp/" + IMAGES_SUBDIR + "/" + str(i) + ".jpg", COLOR_RGB)
      process_image(image)
  else:
    IMAGES_SUBDIR = "comp/buoys_1"
    
    image_count = 0
    for i in range(1584, 1687):
      image = load_image("/home/jam/projects/forward-vision/images/" + IMAGES_SUBDIR + "/" + str(i) + ".jpg", COLOR_RGB)
      x, y, confidence = process_image(image)
      image_count += 1
      #pack and publish results to DSM buffer
      pub_loc(client, 0, x, y, confidence, image_count % 256)
      #l = Location()
      #l.x = 0
      #l.y = x
      #l.z = y
      #l.confidence = confidence

      #buf = Pack(l)
      #client.setLocalBufferContents(TARGET_LOCATION, buf)
      #print("[main] [dsm] publishing x: " + str(l.x) + " y: " + str(l.y) + " z: " + str(l.z) + " c: " + str(l.confidence))

#conditional imports in live mode
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

