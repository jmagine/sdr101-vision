import logging
import utils

log = logging.getLogger(__file__)

from picamera.array import PiRGBArray
except:

class Camera():
	
	
class PiCamera(Camera):
	this.resolution = (2592, 1944)
	pass

def get_camera():
	if ON_PI:
		return PiCamera()
	else:
		return Camera()