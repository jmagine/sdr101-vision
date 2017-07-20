import time
import logging

import utils

log = logging.getLogger(__file__)

if utils.ON_PI:
	import picamera
	import picamera.array

def setup_camera(camera):

class Camera():
	def __init__(self):
		pass

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def close(self):
		pass

	def setup(self):
		pass

class OpenCVCamera(Camera):
	def __init__(self, camera_id=0):
		self._camera = cv2.VideoCapture(camera_id)

	def close(self):
		self._camera.release()

	def frame(self):
		return self._camera.read()

	
class PiCamera(Camera):
	def __init__(self):
		self.resolution = (2592, 1944)
		pass

class PiCamera2(Camera):
	def __init__(self, resolution=(1024, 768), downsize=(320, 240)):
		self._camera = picamera.PiCamera()
		self._stream = picamera.array.PiRGBArray(self._camera)
		self._camera.resolution = resolution
		self.downsize = downsize

		time.sleep(2)

	def next_frame(self):
		self._camera.capture(self._stream, format='bgr', resize=self.downsize)
		return self._stream

	def close(self):
		self._camera.close()

	def setup(self):
	    self._camera.sharpness = 0
	    self._camera.contrast = 0
	    self._camera.brightness = 50
	    self._camera.saturation = 0
	    self._camera.ISO = 0
	    self._camera.video_stabilization = False
	    self._camera.exposure_compensation = 0
	    self._camera.exposure_mode = 'auto'
	    self._camera.meter_mode = 'average'
	    self._camera.awb_mode = 'auto'
	    self._camera.image_effect = 'none'
	    self._camera.color_effects = None
	    self._camera.rotation = 0
	    self._camera.hflip = False
	    self._camera.vflip = False
	    self._camera.crop = (0.0, 0.0, 1.0, 1.0)
	    self._camera.resolution = (2592,1944)
	    self._camera.framerate = 5


def get_camera():
	if ON_PI:
		return PiCamera()
	else:
		return Camera()