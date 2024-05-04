import picarx
from  picarx import Picarx
from time import sleep

class Motor(object):

    def __init__(self, px_instance):
        #self.px = Picarx()
        self.px = px_instance
        self.is_moving = False 
        
    # TODO timers for all actions:
    def forward(self, speed=0.7):
        self.is_moving = True
        self.px.forward(speed)
        print("Motor Forward")
    
    def backward(self, speed=0.7):
        self.is_moving = True
        self.px.backward(speed)
        print("Motor backward")
        
    def right(self):
        self.px.set_dir_servo_angle(35)
    
    def left(self):
        self.px.set_dir_servo_angle(-35)
        
    def straight(self):
        self.px.set_dir_servo_angle(0)
    
    def stop(self):
        self.is_moving = False
        self.px.forward(0) #Set speed to zero
    
    def get_status(self):
        return self.is_moving
    
