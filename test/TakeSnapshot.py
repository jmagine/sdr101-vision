import cv2
cap = cv2.VideoCapture(1)
_,img = cap.read()
#for i in range(30):
#    cap.read()

cv2.imwrite('snapshot.png',img)
del(cap)