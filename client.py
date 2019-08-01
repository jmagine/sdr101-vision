import cv2 as cv
import io
import socket
import struct
import time
import pickle
import threading

disp_forward = True
disp_downward = True
forward_host = "10.0.1.2"
forward_port = 5000
downward_host = "10.0.1.2"
downward_port = 5001
res_display = (480, 360)
num_rows = 1
num_cols = 3

class vision_client(threading.Thread):
  def __init__(self, host, port, name):
    super(vision_client, self).__init__()
    self.daemon = True
    self.host = host
    self.port = port
    self.name = name

  def run(self):
    while True:
      try:
        print("[client][%s] connecting to: %s:%d" % (self.name, self.host, self.port))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.host, self.port))
        conn = client_socket.makefile('rb')
        break
      except Exception as e:
        print("[client][%s] Error: %s" % (self.name, str(e)))
    
    try:
      data = b""
      payload_size = struct.calcsize(">L")
      print("[client][%s] payload_size: %d" % (self.name, payload_size))
      while True:
          while len(data) < payload_size:
              #print("Recv: {}".format(len(data)))
              data += client_socket.recv(4096)

          print("[client][%s] recv: %d" %(self.name, len(data)))
          packed_msg_size = data[:payload_size]
          data = data[payload_size:]
          msg_size = struct.unpack(">L", packed_msg_size)[0]
          #print("msg_size: {}".format(msg_size))
          while len(data) < msg_size:
              data += client_socket.recv(4096)
          frame_data = data[:msg_size]
          data = data[msg_size:]

          frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
          frame = cv.imdecode(frame, cv.IMREAD_COLOR)
          frame = cv.resize(frame, (res_display[0] * num_cols, res_display[1] * num_rows), interpolation = cv.INTER_CUBIC)
          cv.imshow(self.name, frame)
          key = cv.waitKey(1)
          if key == ord("q"):
            break

    except Exception as e:
      print(str(e)) 
    
    print("[client][%s] disconnecting from: %s:%d" % (self.name, self.host, self.port))

if __name__ == "__main__":
  if disp_forward:
    forward_client = vision_client(forward_host, forward_port, "forward")
    forward_client.start()
  if disp_downward:
    downward_client = vision_client(downward_host, downward_port, "downward")
    downward_client.start()

  while True:
    try:
      time.sleep(1)
    except KeyboardInterrupt:
      print("[main] Ctrl+c detected, terminating")
      break