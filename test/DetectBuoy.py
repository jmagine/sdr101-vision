import cv2
import numpy as np
from cv2 import WINDOW_NORMAL, COLOR_BGR2HSV, waitKey

def nothing(x):
    pass
'''
notes
minimum distance 100+
maxradius ~ 150
param1 = 60
param2 = 10
minradius 0

'''
# http://www.pyimagesearch.com/2014/08/04/opencv-python-color-detection/
cv2.namedWindow('detected circles', flags=cv2.WINDOW_NORMAL)
cv2.createTrackbar('param1', 'detected circles', 0, 100, nothing)
cv2.createTrackbar('param2', 'detected circles', 0, 100, nothing)
cv2.createTrackbar('minRadius', 'detected circles', 0, 500, nothing)
cv2.createTrackbar('maxRadius', 'detected circles', 0, 500, nothing)
cv2.createTrackbar('minimum distance', 'detected circles', 0, 200, nothing)

cv2.setTrackbarPos('param1', 'detected circles', 60)
cv2.setTrackbarPos('param2', 'detected circles', 10)
cv2.setTrackbarPos('minRadius', 'detected circles', 0)
cv2.setTrackbarPos('maxRadius', 'detected circles', 150)
cv2.setTrackbarPos('minimum distance', 'detected circles', 100)


filename = 'buoytest5.png'

cimg = cv2.imread(filename)
gimg = cv2.imread(filename, 0)
gimg = cv2.medianBlur(gimg, 5)
cv2.imshow('poop', gimg)
hsvimg = cv2.cvtColor(cimg, COLOR_BGR2HSV);




ORANGE_MIN = np.array([-15, 50, 50], np.uint8)
ORANGE_MAX = np.array([15, 255, 255], np.uint8)




while(1):
    img = cimg.copy()
    p1 = cv2.getTrackbarPos('param1', 'detected circles')
    p2 = cv2.getTrackbarPos('param2', 'detected circles')
    minR = cv2.getTrackbarPos('minRadius', 'detected circles')
    maxR = cv2.getTrackbarPos('maxRadius', 'detected circles')
    mindist = cv2.getTrackbarPos('minimum distance', 'detected circles')
    if p2 != 0 and p1 != 0 and mindist != 0:
        circles = cv2.HoughCircles(gimg, cv2.HOUGH_GRADIENT, 1, mindist, param1=p1, param2=p2, minRadius=minR, maxRadius=maxR)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            pix = np.array([[cimg[i[1], i[0]]]])
            hue = cv2.cvtColor(pix, COLOR_BGR2HSV)[0, 0][0]
            #print(hue)
            if (hue < 180 and hue > 130) or (hue > 0 and hue < 30):
                cv2.circle(img, (i[0], i[1]), i[2], (0, 255, 128), 2)
                cv2.circle(img, (i[0], i[1]), 2, (0, 255, 0), 3)   
            else :
                cv2.circle(img, (i[0], i[1]), i[2], (0, 0 , 255), 2)
                cv2.circle(img, (i[0], i[1]), 2, (0, 0, 255), 3)
    cv2.imshow('detected circles', img)
    cv2.waitKey(0)
cv2.destroyAllWindows()
