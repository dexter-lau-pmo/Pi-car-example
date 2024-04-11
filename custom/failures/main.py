from picarx import Picarx
from vilib import Vilib
from move import Move
from vision_calibration import CVThread
from direction import Direction
from motor import Motor


def main():
    px = Picarx()
    Vilib.camera_start()
    Vilib.display()
    Vilib.pose_detect_switch(True)
    move_bool_array = [False, False]
    motor = Move()

    cv_thread = CVThread(px, move_bool_array)
    direction_thread = Direction(px, move_bool_array)
    motor_thread = Motor(motor, move_bool_array)

    cv_thread.start()
    direction_thread.start()
    motor_thread.start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        px.stop()
        pass
