import numpy as np
import cv2

cap = cv2.VideoCapture(1)

def nothing(x):
    pass

while True:
    #_,img = cap.read()
    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.imread('')
    gray = cv2.imread('',0)
    _,thresh = cv2.threshold(gray,127,255,0)

    _,contours,h = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        approx = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)
        #print len(approx)
        if len(approx)==5:
            #print "pentagon"
            cv2.drawContours(img,[cnt],0,255,-1)
        elif len(approx)==3:
            #print "triangle"
            cv2.drawContours(img,[cnt],0,(0,255,0),-1)
        elif len(approx)==4:
            #print "square"
            cv2.drawContours(img,[cnt],0,(0,0,255),-1)
        elif len(approx) == 8:
            #print "half-circle"
            cv2.drawContours(img,[cnt],0,(255,255,0),-1)
        elif len(approx) > 15:
            #print "circle"
            cv2.drawContours(img,[cnt],0,(0,255,255),-1)

    cv2.imshow('image',img)