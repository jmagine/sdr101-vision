import cv2
import numpy as np
from cv2 import WINDOW_NORMAL, COLOR_BGR2HSV, waitKey

def nothing(x):
    pass

# http://www.pyimagesearch.com/2014/08/04/opencv-python-color-detection/
cv2.namedWindow('detected circles', flags=cv2.WINDOW_NORMAL)



filename = 'buoytest2.jpg'

cimg = cv2.imread(filename)
gimg = cv2.imread(filename, 0)




while(1):
    img = cimg.copy()
    ret,thresh = cv2.threshold(gimg,127,255,1)
    #thresh = cv2.Canny(img,100,200)
    _,contours,h = cv2.findContours(thresh,1,2)
    for cnt in contours:
        
        approx = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)
        if (len(approx)<4):
            cv2.drawContours(img,[cnt],0,(0,255,0),-1)
        elif (len(approx)>20):
            cv2.drawContours(img,[cnt],0,(0,255,255),-1)
        else:
            cv2.drawContours(img,[cnt],0,(0,0,255),-1)
        cv2.imshow('detected circles', img)
        #cv2.waitKey(1)
        '''
        print len(approx)
        if len(approx)==5:
            print "pentagon"
            cv2.drawContours(img,[cnt],0,255,-1)
        elif len(approx)==3:
            print "triangle"
            cv2.drawContours(img,[cnt],0,(0,255,0),-1)
        elif len(approx)==4:
            print "square"
            cv2.drawContours(img,[cnt],0,(0,0,255),-1)
        elif len(approx) == 9:
            print "half-circle"
            cv2.drawContours(img,[cnt],0,(255,255,0),-1)
        elif len(approx) > 15:
            print "circle"
            cv2.drawContours(img,[cnt],0,(0,255,255),-1)
        '''
    cv2.waitKey(0)
cv2.destroyAllWindows()
