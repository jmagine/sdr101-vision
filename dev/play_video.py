import numpy as np
import cv2

cap = cv2.VideoCapture("video_image_samples.MP4")


ret, frame = cap.read()

print(cap.isOpened())
cv2.imshow("frame", frame)
cv2.waitKey(0)

while cap.isOpened():
    ret, frame = cap.read()
    print("naw")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    cv2.imshow("frame", gray)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
