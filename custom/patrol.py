from picarx import Picarx
from timer import Timer
from motor import Motor
import threading
import random

#UNUSED CLASS, FOR FUTURE USE WHEN BLUETOOTH LOCALIZATION WORKS

class Patroller(object):
    def __init__(self, px, motor):
        self.px = px
        self.motor = motor
        self.patrol_timer = Timer()
    
    def patrol(self):
        self.motor.forward(10)
        self.px.set_cam_tilt_angle(20)
        self.px.set_cam_pan_angle(0)
        if self.patrol_timer.is_timelapse_over():
            self.patrol_timer.new_timer(30)
            rand_angle = random.randint(-35,35)
            self.px.set_dir_servo_angle(rand_angle)
            threading.Timer(3, self.motor.straight).start()
