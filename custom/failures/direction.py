# cv_thread.py
import threading
from time import sleep
from vilib import Vilib
from picarx import Picarx

class Direction(threading.Thread):
    def __init__(self, px, move_bool_array):
        super(Direction, self).__init__()
        self.px = px
        self.move_bool_array = move_bool_array
        
    def run(self):
        x_angle =0
        y_angle =0
        while True:
            joints = Vilib.detect_obj_parameter['body_joints']
            if joints and (len(joints) >= 12) and joints[11] and joints[12]:
                coordinate_x = ((joints[11][0] + joints[12][0]) / 2)*640
                coordinate_y = ((joints[11][1] + joints[12][1]) / 2)*480
            
                # change the pan-tilt angle for track the object
                x_angle +=(coordinate_x*10/640)-5
                x_angle = self.clamp_number(x_angle,-70,70)
                self.px.set_cam_pan_angle(x_angle)
                self.px.set_dir_servo_angle(x_angle / 2)

                y_angle -=(coordinate_y*10/480)-5
                y_angle = self.clamp_number(y_angle,-10,75)
                self.px.set_cam_tilt_angle(y_angle)
                sleep(0.1)
                
                if coordinate_x >= 640*(3/4) or coordinate_x <= 640*(1/4):
                    self.update_boolean_move(True)
                else:
                    self.update_boolean_move(False)
            
    def clamp_number(self, num, a, b):
        return max(min(num, max(a, b)), min(a, b))

    def update_boolean_move(self, isMove):
        self.move_bool_array[1] = isMove
