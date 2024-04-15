from time import sleep,strftime,localtime
from vilib import Vilib
from motor import Motor
from timer import Timer 
from follower import Follower
from patrol import Patroller
from camera import Camera
import threading

class AutoPilot(threading.Thread):
    
    def __init__(self, px, motor):
        super(AutoPilot, self).__init__()
        self.event = threading.Event()
        self.motor = motor
        self.rec_flag = False
        self.record_buffer = Timer() 
        from follower import Follower
        #self.patroller = Patroller(px, motor) #unused
        self.follower = Follower(px, motor)
        self.cam = Camera() 
        
    def clamp_number(self, num, a, b):
        return max(min(num, max(a, b)), min(a, b))

    def run(self):
          
        while True:
            self.event.wait()
            #print("AUTO MODE ON")
            joints = Vilib.detect_obj_parameter['body_joints']
            #print("joints")
            #person is in frame
            if joints and (len(joints) >= 12) and joints[11] and joints[12]: #11 is left shoulder point, 12 is right shoulder point
                #print("SHOULDERS DETECTED")
                self.follower.follow(joints)
                
                if self.rec_flag == False:
                    self.rec_flag = True
                    self.cam.start_record() #Removed from Youwei code Camera class
                    self.record_buffer.new_timer(time=3) #ensure every last frame recorded will always have 3 seconds buffer before video ends 
                
            #stops and wait for person to move back in frame, if he does
            elif self.rec_flag:
                #is recording, wait for any new visual feedback
                self.motor.stop()
            
            # TODO: Patroller Class
            #else:
                #self.patroller.patrol()
                
            if self.rec_flag and self.record_buffer.is_timelapse_over(): #Removed from Youwei code Camera class
                self.rec_flag = False
                self.cam.stop_record() #Removed from Youwei code Camera class


