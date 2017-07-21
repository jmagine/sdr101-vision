import cv2
import numpy as np

# HSV Thresholds
lower_blue = np.array([110, 50, 50])
upper_blue = np.array([130, 255, 255])

def main():
    cap = cv2.VideoCapture(0)
    try:
        while True:
            # Take each frame
            ret, frame = cap.read()

            # Convert BGR to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Threshold the HSV image to get only blue colors
            mask = cv2.inRange(hsv, lower_blue, upper_blue)

            # Bitwise-AND mask and original image
            res = cv2.bitwise_and(frame,frame, mask= mask)

            cv2.imshow('frame',frame)
            cv2.imshow('mask',mask)
            cv2.imshow('res',res)
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
    finally:
        cap.release()

if __name__ == '__main__':
    main()