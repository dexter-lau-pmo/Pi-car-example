#from picarx import Picarx
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
            
    def make_eye_contact(self, joints): #controls Camera
        '''
        #Original code block relies on 11/12 shoulders only
        # change the pan-tilt angle for track the object
        self.coordinate_x = ((joints[11][0] + joints[12][0]) / 2)*640 #Center around the x-coordinate
        self.coordinate_y = ((joints[11][1] + joints[12][1]) / 2)*480 #Centre around the y-coordinate
        '''
        
        #Try to center around face and shoulders
        #n = 0 #Count for joint number
        x_sum = 0 #total x coordinate sum, to use for averaging
        y_sum = 0 #total y coordinate sum, to use for averaging
        num_valid_joints = 0  #Number of joints with non-zero coordinates
        
        for n in range(7,12): #Only use jointss 7-12, face and shoulders: Please see https://github.com/google/mediapipe/blob/master/docs/solutions/pose.md for number details
                if joints[n][0]>0 and joints[n][1]>0 and (n>6 and n<13): #if joint coordinates are non zero, add them into the average
                        x_sum = x_sum + joints[n][0]
                        y_sum = y_sum + joints[n][1]

                        num_valid_joints += 1
                if (joints[n][0]<=0 or joints[n][1]<=0) and (n>6 and n<13): #if joint coordinates are zero, they are invalid for use
                        print("Invalid joint ", n)
                n += 1 #increment count
        
        if num_valid_joints <1: #Exit immediately if number of valid joints is zero
                return
        
        self.coordinate_x = (x_sum/num_valid_joints)*640 #Center around the x-coordinate
        self.coordinate_y = (y_sum/num_valid_joints)*480 #Centre around the y-coordinate
        print("Number of non-zero joints ", num_valid_joints)
        print("X , Y: " , self.coordinate_x , " " , self.coordinate_y)
        
        
        self.x_angle += (self.coordinate_x*10/640)-5
        self.x_angle = self.clamp_number(self.x_angle,-70,70)
        #print("X_ANGLE: ", self.x_angle)
        self.px.set_cam_pan_angle(self.x_angle)
        
        self.y_angle -= (self.coordinate_y*10/480)-5
        self.y_angle = self.clamp_number(self.y_angle,0,80)
        #print("Y_ANGLE: ", self.y_angle)
        self.px.set_cam_tilt_angle(self.y_angle)
        sleep(0.1)
        
        
    def stalk_person(self, joints): #controls motor
        # proximity check
        '''
        filtered_list = list(filter(lambda x : x is not None, joints)) #Uses all joints here for some reason?
        x_list = list(map(lambda x : x[0], filtered_list)) #list of all x-coordinates
        y_list = list(map(lambda x : x[1], filtered_list)) #list of all y-coordinates
                
        max_y = max(y_list) * 480
        max_x = max(x_list) * 640
        min_y = min(y_list) * 480
        min_x = min(x_list) * 640
        '''
        max_y = 0
        max_x = 0
        min_y = 9999
        min_x = 9999
        num_valid_joints = 0
        for n in range(7,12): #Only use jointss 7-12, face and shoulders: Please see https://github.com/google/mediapipe/blob/master/docs/solutions/pose.md for number details
                if joints[n][0]>0 and joints[n][1]>0 and (n>6 and n<13): #x
                        if max_y<joints[n][1]:
                                max_y = joints[n][1]
                        if min_y>joints[n][1]:
                                min_y = joints[n][1]
                        if max_x < joints[n][0]:
                                max_x = joints[n][0]
                        if min_x>joints[n][0]:
                                min_x = joints[n][0]
                        num_valid_joints += 1
        
        if num_valid_joints <1: #Exit immediately if number of valid joints is zero
                print("No valid joints, dont follow")
                self.motor.stop()
                return

                
        max_y = max_y * 480
        max_x = max_x * 640
        min_y = min_y * 480
        min_x = min_x * 640
        print("max_x , max_y, min_x , min_y", max_x , max_y, min_x , min_y)

        human_area = (max_x - min_x) * (max_y - min_y)
        coverage_ratio = human_area / (640 * 480)
        
        if num_valid_joints == 2 and joints[11] and joints[12]: #If we see from back only, there is only one dimension
                coverage_ratio = (max_x - min_x)/640 * 0.7 # add an offset, as shoulders can be further but still follow
        
        print("Coverage" , coverage_ratio)
        
        
        self.px.set_dir_servo_angle(self.x_angle / 2)

        #if coverage_ratio <= 0.39 or self.coordinate_x >= 640*(4/5) or self.coordinate_x <= 640*(1/5):
        if coverage_ratio <= 0.1 and coverage_ratio > 0.01: #Extra condition, so that if coverage ratio = 0 due to only one joint, won't count
            print("Moving to follow hooman")
            self.motor.forward()
        else:
            print("Hooman sufficiently close")
            self.motor.stop()
