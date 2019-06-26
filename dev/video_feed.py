import numpy as np
import cv2


def main():
    camera = cv2.VideoCapture(0)
    frames = []
    try:
        while True:
            ret, capture = camera.read()
            frames.append(capture)
            while len(frames) > 2:
                frames.pop(0)

            frame = np.array(np.mean(frames, axis=0), dtype=np.uint8)
            # Our operations on the frame come here
            # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Display the resulting frame
            cv2.imshow("frame", frame)
            if cv2.waitKey(1) == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
