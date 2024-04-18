from picarx import Picarx
from vilib import Vilib
from auto_pilot import AutoPilot
from motor import Motor
from mqtt_client import MQTTClient
from position_estimate import PositionEstimator
import time
from time import sleep
import fcntl
import json
from datetime import datetime

#For auto
from follower import Follower
from patrol import Patroller
from camera import Camera

JSON_FILE_PATH = '/home/admin/picar-x/custom/REST/data.json'
POWER = 50
SAFE_DISTANCE = 20   # > 40 safe
DANGER_DISTANCE = 10 # > 20 && < 40 turn around, 
                    # < 20 backward

class App(object):
    def __init__(self):
        self.x_coordinate = 0
        self.y_coordinate = 0
        self.mqtt_client = MQTTClient()
        self.px = Picarx()
        #self.motor = Motor()
        self.motor = Motor(self.px)
        #self.auto = AutoPilot(self.px, self.motor)
        #self.auto.start() #Start auto pilot handling thread
        self.is_avoiding_collision = False
        self.alert_x1 = 0.0
        self.alert_x2 = 1.0
        self.alert_y1 = 0.0
        self.alert_y2 = 1.0    
        self.auto_flag = True
        
        #imported from auto thread:
        self.rec_flag = False
        #self.record_buffer = Timer() 
        #self.patroller = Patroller(px, motor) #unused
        self.follower = Follower(self.px, self.motor)
        self.cam = Camera()
    
    # TODO: clear json file value after reading it
    def run(self):
        self.mqtt_client.connect() #disable for my sanity when wifi is bad
        last_msg_time = time.time() - 40 #To start first message immediately
        self.mqtt_client.stop_car == True
        
        #while True: #Motor testing only
         #   self.camera_nod()
          #  self.camera_shake()
            
            
        self.px.set_cam_tilt_angle(25)
        
        
        while True:
            n=0
            try:
                with open(JSON_FILE_PATH, 'r') as file:
                    fcntl.flock(file, fcntl.LOCK_SH)
                    data = json.load(file)
                    fcntl.flock(file, fcntl.LOCK_UN)
            except json.decoder.JSONDecodeError as json_err: #If JSON file gets corrupted, infinite loop might occur if not handled properly
                if n<20:
                    continue
                else:
                     n=0
                     print("\n JSON Error, default to stop \n")
                     self.change_mode_stop()
                     
            insn = data['instruction'] #get current mode (manual/auto) from the JSON file loaded earlier
            
            #Bluetooth localisation # commented off to remove feature & reduce lag
            #self.update_bot_coordinates() #calculate the bot position
            #self.update_alert_zone()#if you got a message that updates the bots alert zone, update it

            #Process special statuses
            if self.mqtt_client.drive_towards_camera == True: #If you get a message "names" from the Camera Drive forward and change to auto mode. This simulates finding the camera
                print("\n\n\nDriving to camera\n\n\n\n")
                self.drive_towards_camera()
                self.mqtt_client.drive_towards_camera = False
            
            elif self.mqtt_client.stop_car == True: #If you get a message to change car mode to stop, do so
                print("changing to stop mode")
                self.change_mode_stop()
                self.mqtt_client.stop_car = False
                insn == "stop"
                
            elif self.mqtt_client.auto_car == True: # if you get a message tochange car mode to auto, do so
                print("changing to auto mode")
                self.change_mode_auto()
                self.mqtt_client.auto_car = False 
                insn == "auto"
            
            #Check for Cam zone
            if self.get_cam_zone() != "NULL":
                if insn == "auto":
                    self.send_mqtt_update("auto")
                else:
                    self.send_mqtt_update("manual")
            
            
            if insn == "auto": #If current mode is auto , we make the robot follow people arond
                time_elapsed = time.time() - last_msg_time
                if time_elapsed >40:
                    last_msg_time = time.time()
                    self.send_mqtt_update("Auto")
                    print("Auto")
                    
               
                #Collision avoidance
                distance = round(self.px.ultrasonic.read(), 2)
                if distance >= SAFE_DISTANCE or distance <0 : #sensor gives -1 when it fails to receive ultrasonic feedback
                    if self.is_avoiding_collision:
                        self.motor.stop()
                        self.is_avoiding_collision = False
                        
                    #self.auto.event.set() # unpauses auto thread
                    
                    if distance <0:
                        print("Ultrasound error" , distance)
                    
                elif distance >= DANGER_DISTANCE: #within danger distance
                    print("Turning to avoid collision")
                    print(distance)
                    #self.auto.event.clear() # pauses the auto thread
                    self.is_avoiding_collision = True
                    self.motor.right()
                    self.motor.forward()
                    sleep(1)
                else: 
                    #self.auto.event.clear() # pauses the auto thread
                    self.is_avoiding_collision = True
                    print("HIT")
                    print(distance)
                    self.motor.straight()
                    self.motor.backward()
                    sleep(1)
                    
                #Implement auto mode in parallel to tthe other things
                joints = Vilib.detect_obj_parameter['body_joints']
                if joints and (len(joints) >= 12) and joints[11] and joints[12]: #11 is left shoulder point, 12 is right shoulder point
                    #print("SHOULDERS DETECTED")
                    self.follower.follow(joints)
                                    
            else: #If mode is manual, we check a JSON file for instructions on how to move
                
                time_elapsed = time.time() - last_msg_time
                #self.auto.event.clear()
                if time_elapsed >40:
                    last_msg_time = time.time()
                    self.send_mqtt_update("Manual")
            
                if insn == "forward":
                    #self.auto.event.clear()
                    self.motor.forward()
                elif insn == "left":
                    #self.auto.event.clear()
                    self.motor.left()
                elif insn == "right":
                    print("RIGHT")
                    #self.auto.event.clear()
                    self.px.set_dir_servo_angle(35)
                elif insn == "backward":
                    #self.auto.event.clear()
                    self.motor.backward()
                elif insn == "straight":
                    #self.auto.event.clear()
                    self.motor.straight()
                elif insn == "stop":
                    #self.auto.event.clear()
                    self.motor.stop()
                    self.motor.straight()
                    self.px.set_cam_tilt_angle(25)
                    
                    
    def send_mqtt_update(self, mode):

        current_timestamp = datetime.now().isoformat() # add timestamp param
        #print("\n Current time:", current_timestamp)        
        message = {
            #Comment out x and y coordinates because not reporting coordinates
            #"x" : self.x_coordinate,
            #"y" : self.y_coordinate,
            "status" : self.motor.get_status(),
            "mode" : mode,
            "camera-zone": self.get_cam_zone(),
            "timestamp": current_timestamp
        }
        self.mqtt_client.publish(message)
        print(message)

    def update_bot_coordinates(self):
        pos_estimator = PositionEstimator()
        self.x_coordinate, self.y_coordinate = pos_estimator.get_coordinates()
        #self.x_coordinate, self.y_coordinate = pos_estimator.trilaterate() #old calulating funcation, deprecated for a better one
    
    def update_alert_zone(self):
        #Update Alert zone areas
        self.alert_x1 = self.mqtt_client.x1
        self.alert_x2 = self.mqtt_client.x2
        self.alert_y1 = self.mqtt_client.y1
        self.alert_y2 = self.mqtt_client.y2
        
        
    #Returns camera if in zone, otherwise, returns "NULL"
    def get_cam_zone(self):
        if self.check_color_is_white():# An alternate way to trigger the camera zone is for robot to run over white stuff
            print("ITS WHITE")
            return "urn:ngsi-ld:Camera:Camera001"
            
        #arbitrary dummy zone for camera where cam field is x is 1 to 10, y is 1 to 10
        #Commented out this portion as not longer checking for coordinates
        #if self.x_coordinate < self.alert_x2 and self.y_coordinate < self.alert_y2 and self.x_coordinate > self.alert_x1 and self.y_coordinate > self.alert_y1:
            #return "urn:ngsi-ld:Camera:Camera001"

        else:
            return "NULL"
    
    def drive_towards_camera(self):
        self.mqtt_client.drive_towards_camera = False
        last_msg_time = time.time()
        timelapse = time.time() - last_msg_time
        self.motor.straight()
        self.motor.forward()
        
        while timelapse < 4 :
            timelapse = time.time() - last_msg_time
            if(self.get_cam_zone() == "urn:ngsi-ld:Camera:Camera001"):
                print("Entered Cam Zone")
                break
            print("drive towards camera")
            sleep(0.01) #Try if sleep helps
            
        print("Stopped driving to camera") 
        self.motor.stop()
        json_data = {"instruction":"auto"}
        json_object = json.dumps(json_data)
        print("Attempt to update JSON")
        self.write_file(JSON_FILE_PATH, json_object)
            
    def write_file(self, filename, fileinput):
        while True:
            print("File write attempt")
            try:
                with open(filename, "w") as file:
                    fcntl.flock(file, fcntl.LOCK_EX)
                    file.write(fileinput)
                    fcntl.flock(file, fcntl.LOCK_UN)
                    print("File write success")
                    break
            except Exception as e:
                print("File Error occurred:", str(e))
                                        
    def change_mode_auto(self):
        json_data = {"instruction":"auto"}
        json_object = json.dumps(json_data)
        self.write_file(JSON_FILE_PATH,str(json_object) )

    def change_mode_stop(self):
        json_data = {"instruction":"stop"}
        json_object = json.dumps(json_data)
        self.write_file(JSON_FILE_PATH,str(json_object) )
        
    def check_color_is_white(self):
        current_grayscale_value = self.px.get_grayscale_data()
        return all(list(map(lambda x: x > 120, current_grayscale_value)))
    
    #Hardware testing functions
    def camera_nod(self): 
        print("Nod")
        self.px.set_cam_tilt_angle(25)
        sleep(2)
        self.px.set_cam_tilt_angle(-25)
        sleep(2)
        self.px.set_cam_tilt_angle(0)
    def camera_shake(self):
        print("Shake")
        self.px.set_cam_pan_angle(25)
        sleep(2)
        self.px.set_cam_pan_angle(-25)
        sleep(2)
        self.px.set_cam_pan_angle(0)
        sleep(3)
        self.motor.left()
        sleep(2)
        self.motor.right()
        sleep(2)
        self.motor.straight()
        sleep(2)
        print("Attempt forward")
        self.px.forward(1)
        sleep(2)
        print("Stop")
        self.px.forward(0)
        sleep(1)
        print("Attempt backward")
        self.px.backward(1)
        sleep(2)
        print("Stop")
        self.px.forward(0)
        sleep(1)
        
if __name__ == '__main__':
    try:
        app =App()
        app.run()
    except KeyboardInterrupt:
        app.motor.stop()
        pass
