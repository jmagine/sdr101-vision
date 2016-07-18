import cv2
import numpy as np
# from matplotlib import pyplot as plt

def update(x):
    global frame
    
    edges = cv2.Canny(frame, cv2.getTrackbarPos('thresh1', 'frame'), cv2.getTrackbarPos('thresh2', 'frame'))
    cv2.imshow('frame', edges)
    pass

# cap = cv2.VideoCapture(0)
cv2.namedWindow('frame')

frame = cv2.imread('buoytest3.jpg')
while(1):
    update(None)
    cv2.createTrackbar('thresh1', 'frame', 0, 300, update)
    cv2.createTrackbar('thresh2', 'frame', 0, 300, update)
    cv2.setTrackbarPos('thresh1', 'frame', 200)
    cv2.setTrackbarPos('thresh2', 'frame', 100)
    if cv2.waitKey(0) == ord('q'):
        break
cv2.destroyAllWindows()
