#from time import sleep,strftime,localtime
import time
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
        #self.record_buffer = Timer() 
        #self.patroller = Patroller(px, motor) #unused
        self.follower = Follower(px, motor)
        self.cam = Camera() 
        #self.start_time = time.time()
        
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
                
                #if self.rec_flag == False:
                    #self.rec_flag = True
                    #self.cam.start_record() #Removed from Youwei code Camera class
                    #self.record_buffer.new_timer(time=3) #ensure every last frame recorded will always have 3 seconds buffer before video ends 
                    #self.start_time = time.time()
                    
            #stops and wait for person to move back in frame, if he does
            #elif self.rec_flag:
                #is recording, wait for any new visual feedback
                #self.motor.stop() #Motor stops if nothing for 3 seconds
            
            # TODO: Patroller Class
            #else:
                #self.patroller.patrol()
                
            #timelapse = time.time() - start_time()
            
            #if self.rec_flag and self.record_buffer.is_timelapse_over(): #Removed from Youwei code Camera class
            #if self.rec_flag and timelapse > 3:
                #self.rec_flag = False
                #self.cam.stop_record() #Removed from Youwei code Camera class


