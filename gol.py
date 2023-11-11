import pyvirtualcam
import numpy as np
import cv2

import gol_core

CAMERA_ID = 0
DEVICE_PATH = '/dev/video5'

vc = cv2.VideoCapture(CAMERA_ID)

pref_width = 1280
pref_height = 720
pref_fps_in = 30
vc.set(cv2.CAP_PROP_FRAME_WIDTH, pref_width)
vc.set(cv2.CAP_PROP_FRAME_HEIGHT, pref_height)
vc.set(cv2.CAP_PROP_FPS, pref_fps_in)

# Query final capture device values (may be different from preferred settings).
WIDTH = int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
HEIGHT = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
FPS = vc.get(cv2.CAP_PROP_FPS)

CELL_SIZE = 16

grid = gol_core.GameOfLife(size=(int(HEIGHT / CELL_SIZE), int(WIDTH / CELL_SIZE)))

def main(): 
    with pyvirtualcam.Camera(width=WIDTH, height=HEIGHT, fps=20, device=DEVICE_PATH) as cam:
        print(f'Using virtual camera: {cam.device}')
        while True:
            grid.run_board()
            # Frame stuff
            ret, frame = vc.read()
            if not ret:
                raise RuntimeError('Error fetching frame')

            scaled_board = grid.board.repeat(CELL_SIZE, axis=0).repeat(CELL_SIZE, axis=1)
            # BGR => RGB
            frame = frame[...,::-1]
            frame[:, :, 0] = frame[:, :, 0] * scaled_board
            frame[:, :, 1] = frame[:, :, 1] * scaled_board
            frame[:, :, 2] = frame[:, :, 2] * scaled_board

            result = np.array(frame)
            cam.send(result)
            cam.sleep_until_next_frame()


if __name__ == "__main__":
    main()
