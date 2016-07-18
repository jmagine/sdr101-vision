import cv2
import numpy as np
# from matplotlib import pyplot as plt

def update(x):
    global hsv
    edges = cv2.Canny(frame, cv2.getTrackbarPos('thresh1', 'frame'), cv2.getTrackbarPos('thresh2', 'frame'))
    cv2.imshow('frame', hsv)
    pass

# cap = cv2.VideoCapture(0)
#cv2.namedWindow('frame')
cv2.namedWindow("res",cv2.WINDOW_NORMAL)
frame = cv2.imread('C:\\Users\\Robert\\Documents\\EclipseWorkspace\\OpenCV\\buoytest6.png')
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
hue_avg = np.average(hsv[:,:,0])
sat_avg = np.average(hsv[:,:,1])
lower_blue = np.array([hue_avg-5,sat_avg-50,0])
upper_blue = np.array([hue_avg+5,sat_avg+50,255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)
mask = cv2.bitwise_not(mask)
res = cv2.bitwise_and(frame,frame, mask=mask)
while(1):
    #update(None)
    cv2.imshow('res',res)
    #cv2.createTrackbar('thresh1', 'frame', 0, 300, update)
    #cv2.createTrackbar('thresh2', 'frame', 0, 300, update)
    #cv2.setTrackbarPos('thresh1', 'frame', 200)
    #cv2.setTrackbarPos('thresh2', 'frame', 100)
    if cv2.waitKey(0) == ord('q'):
        break
cv2.destroyAllWindows()
