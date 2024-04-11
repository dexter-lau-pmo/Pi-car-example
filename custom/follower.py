from picarx import Picarx
from time import sleep
from vilib import Vilib
from motor import Motor

class Follower(object):
    def __init__(self, px, motor):
        self.px = px
        self.motor = motor
        self.x_angle = 0
        self.y_angle = 40
    
    def clamp_number(self, num, a, b):
        return max(min(num, max(a, b)), min(a, b))
    
    def follow(self, joints):
        self.make_eye_contact(joints)
        self.stalk_person(joints)
            
    def make_eye_contact(self, joints):
        # change the pan-tilt angle for track the object
        self.coordinate_x = ((joints[11][0] + joints[12][0]) / 2)*640
        self.coordinate_y = ((joints[11][1] + joints[12][1]) / 2)*480
        
        self.x_angle += (self.coordinate_x*10/640)-5
        self.x_angle = self.clamp_number(self.x_angle,-70,70)
        #print("X_ANGLE: ", self.x_angle)
        self.px.set_cam_pan_angle(self.x_angle)
        
        self.y_angle -= (self.coordinate_y*10/480)-5
        self.y_angle = self.clamp_number(self.y_angle,0,80)
        #print("Y_ANGLE: ", self.y_angle)
        self.px.set_cam_tilt_angle(self.y_angle)
        sleep(0.15)
        
    def stalk_person(self, joints):
        # proximity check
        filtered_list = list(filter(lambda x : x is not None, joints))
        x_list = list(map(lambda x : x[0], filtered_list))
        y_list = list(map(lambda x : x[1], filtered_list))
                
        max_y = max(y_list) * 480
        max_x = max(x_list) * 640
        min_y = min(y_list) * 480
        min_x = min(x_list) * 640
        human_area = (max_x - min_x) * (max_y - min_y)
        coverage_ratio = human_area / (640 * 480)
        print(coverage_ratio)
        
        self.px.set_dir_servo_angle(self.x_angle / 2)

        if coverage_ratio <= 0.2 or self.coordinate_x >= 640*(3/4) or self.coordinate_x <= 640*(1/4):
            self.motor.forward()
        else:
            self.motor.stop()
