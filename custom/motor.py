from picarx import Picarx
from time import sleep

class Motor(object):

    def __init__(self):
        self.px = Picarx()
        self.is_moving = False 
        
    # TODO timers for all actions:
    def forward(self, speed=1):
        self.is_moving = True
        self.px.forward(speed)
    
    def backward(self, speed=1):
        self.is_moving = True
        self.px.backward(speed)
        
    def right(self):
        self.px.set_dir_servo_angle(35)
    
    def left(self):
        self.px.set_dir_servo_angle(-35)
        
    def straight(self):
        self.px.set_dir_servo_angle(0)
    
    def stop(self):
        self.is_moving = False
        self.px.forward(0)
    
    def get_status(self):
        return self.is_moving
    
