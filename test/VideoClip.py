import cv2
import numpy as np

for i in range(1,67):
	frame = cv2.imread('frames/frame%03d.bmp'%i)
	#gimg = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	hue_avg = np.average(hsv[:,:,0])
	sat_avg = np.average(hsv[:,:,1])
	print("sat:"+str(sat_avg))
	print("hue:"+str(hue_avg))
	lower_blue = np.array([hue_avg-7,sat_avg-60,127])
	upper_blue = np.array([hue_avg+7,sat_avg+30,255])
	mask = cv2.inRange(hsv, lower_blue, upper_blue)
	mask = cv2.bitwise_not(mask)
	res = cv2.bitwise_and(frame,frame, mask=mask)
	maxr = 0
	_,contours,h = cv2.findContours(mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
	for cnt in contours:
		maxr = 0
		area = cv2.contourArea(cnt)

		apx = cv2.approxPolyDP(cnt,0.04*cv2.arcLength(cnt,True),True)

		#ratio = area / (np.pi*(radius**2))

		if (len(apx)<3):
			cv2.drawContours(res,[cnt],0,(0,255,0),-1)
		elif (len(apx)>4):
			cv2.drawContours(res,[cnt],0,(0,0,255),-1)
			if cv2.isContourConvex(apx):
				(x,y),radius = cv2.minEnclosingCircle(apx)
				center = (int(x),int(y))
				radius = int(radius)
				cv2.circle(res,center,radius,(127,0,255),3)
		else:
			cv2.drawContours(res,[cnt],0,(0,255,255),-1)
	cv2.imwrite('frames_out/frame%03d.bmp'%i,res)
	print('frame %u'%i)
cv2.destroyAllWindows()