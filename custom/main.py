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
from ftp_uploader import FTPUploader

#For auto
from follower import Follower
from patrol import Patroller
from camera import Camera

#For sound
from robot_hat import Music


JSON_FILE_PATH = '/home/admin/picar-x/custom/REST/data.json'
sound_file_path = "/home/admin/picar-x/custom/sounds/car-double-horn.wav"
POWER = 50
SAFE_DISTANCE = 13   # > 40 safe
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
        self.ftp_uploader = FTPUploader()
        
        #For sound
        self.music = Music()
        self.music.sound_play('../sounds/car-double-horn.wav')
    
    # TODO: clear json file value after reading it
    def run(self):
        self.mqtt_client.connect() #disable for my sanity when wifi is bad
        last_msg_time = time.time() - 40 #To start first message immediately
        self.mqtt_client.stop_car == True
        time_elapsed_since_human_sighted = time.time()
        last_joints_time = time.time()
        last_photo_time = time.time()
        #while True: #Motor testing function only
         #   self.camera_nod()
          #  self.camera_shake()
            
            
        self.px.set_cam_tilt_angle(25)
        
        self.take_and_upload_photo()
        
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
                self.mqtt_client.cctv_camera_direction = "None"
            
            elif self.mqtt_client.stop_car == True: #If you get a message to change car mode to stop, do so
                print("changing to stop mode")
                self.change_mode_stop()
                self.mqtt_client.stop_car = False
                insn = "stop"
                
            elif self.mqtt_client.auto_car == True: # if you get a message tochange car mode to auto, do so
                print("changing to auto mode")
                self.change_mode_auto()
                self.mqtt_client.auto_car = False 
                insn = "auto"
            
            elif self.mqtt_client.override_auto_mode == True:
                print("Mqtt command passed  to over ride")
                self.mqtt_client.override_auto_mode = False 
                
                if insn != "mqtt": #Dont do shit if already in mqtt mode
                    print("changing override auto mode\n change to mqtt")
                    self.change_mode_mqtt()
                    insn = "mqtt"
                #print("Insn ", insn)
            
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
                                            
                    if distance <0:
                        print("Ultrasound error" , distance)
                
                else: 
                    self.is_avoiding_collision = True
                    print("HIT")
                    print(distance)
                    self.motor.straight()
                    self.motor.backward()
                    sleep(1)
                    
                #Implement auto mode in parallel to the other things
                
                joints = Vilib.detect_obj_parameter['body_joints']
                #if joints and (len(joints) >= 12) and joints[11] and joints[12]: #11 is left shoulder point, 12 is right shoulder point #Original code follows shoulders
                if joints and (len(joints) >= 8): #New code to follow as long as sufficient joints are detected
                    self.follower.follow(joints)
                    last_joints_time = time.time()
                        
                    if  time.time() - last_photo_time > 5: #Take a picture if its a new person or every 5 seconds of following
                        self.take_and_upload_photo()
                        last_photo_time = time.time() 
                
                #If haven't seen hooman in the last second, stop the motor
                time_elapsed_since_human_sighted = time.time() - last_joints_time
                
                if time_elapsed_since_human_sighted > 0.5:
                    self.motor.stop()
                    
            
                
            else: #If mode is manual (Not auto), we check a JSON file for instructions on how to move
                
                time_elapsed = time.time() - last_msg_time
                #self.auto.event.clear()
                if time_elapsed >40:
                    last_msg_time = time.time()
                    self.send_mqtt_update("Manual")
                    print("insn is : ", insn)
                
                #Logic -> If Got MQTT command, we remove the auto mode
                
                
                #Control motor via JSON file
                if insn == "forward":
                    self.motor.forward()
                elif insn == "left":
                    self.motor.left()
                elif insn == "right":
                    print("RIGHT")
                    self.px.set_dir_servo_angle(35)
                elif insn == "backward":
                    self.motor.backward()
                elif insn == "straight":
                    self.motor.straight()
                elif insn == "stop":
                    print("Reset angles")
                    self.motor.stop()
                    self.motor.straight()
                    self.px.set_cam_tilt_angle(25) #look up
                    self.px.set_cam_pan_angle(0) # Straight
                
                #control camera servo
                if insn == "mqtt":
                    if self.mqtt_client.servo_dir == "right":
                        self.px.set_cam_pan_angle(25)
                        self.mqtt_client.servo_dir = None
                        print("Cam right")
                    elif self.mqtt_client.servo_dir == "left":
                        self.px.set_cam_pan_angle(-25)
                        self.mqtt_client.servo_dir = None
                        print("Cam left")
                    elif self.mqtt_client.servo_dir == "down":
                        self.px.set_cam_tilt_angle(0)
                        self.mqtt_client.servo_dir = None
                        print("Cam down")
                    elif self.mqtt_client.servo_dir == "up":
                        self.px.set_cam_tilt_angle(30)     
                        self.mqtt_client.servo_dir = None
                        print("Cam up")
                    elif self.mqtt_client.servo_dir == "reset":
                        self.px.set_cam_tilt_angle(25) #look up
                        self.px.set_cam_pan_angle(0) # Straight
                        print("Cam reset")
                        self.mqtt_client.servo_dir = None
                    
                    #Control motor
                    if self.mqtt_client.motor_dir == "forward" :
                        print("Forward")
                        self.motor.forward()
                        self.mqtt_client.motor_dir = None
                    elif self.mqtt_client.motor_dir == "left":
                        print("left")
                        self.motor.left()
                        self.mqtt_client.motor_dir = None
                    elif self.mqtt_client.motor_dir == "right" :
                        print("RIGHT")
                        self.px.set_dir_servo_angle(35)
                        self.mqtt_client.motor_dir = None
                    elif self.mqtt_client.motor_dir == "backward" :
                        print("Backward")
                        self.motor.backward()
                        self.mqtt_client.motor_dir = None
                    elif self.mqtt_client.motor_dir == "straight":
                        self.motor.straight()
                        self.mqtt_client.motor_dir = None
                    elif self.mqtt_client.motor_dir == "stop":
                        print("Reset angles")
                        self.motor.stop()
                        self.motor.straight()
                        self.px.set_cam_tilt_angle(25) #look up
                        self.px.set_cam_pan_angle(0) # Straight
                        self.mqtt_client.motor_dir = None
                        
                    # manual snapshot
                    if self.mqtt_client.motor_dir == "snapshot" or self.mqtt_client.servo_dir == "snapshot":
                        #self.motor.stop()
                        self.take_and_upload_photo()
                        self.mqtt_client.motor_dir = None
                        self.mqtt_client.servo_dir = None
                        print("Photo taken")
                                                    
                                            
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
    
    def take_and_upload_photo(self):
        
        photo_name = "Test" #jpg file type
        # Get the current date and time
        timestamp = datetime.now()
        formatted_timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print("Formatted Timestamp:", formatted_timestamp)
        photo_name = "snapshot_" + formatted_timestamp
        
        print("Take photo")
        file_loc = self.cam.take_photo(photo_name) #Photo location
        gcp_file_loc = "photos/" + photo_name
        gcp_url = self.ftp_uploader.upload_file(file_loc , gcp_file_loc, False)
        print("File destination " , gcp_url)
        
        #MQTT path sent
        current_timestamp = datetime.now().isoformat() # add timestamp param
        #print("\n Current time:", current_timestamp)        
        message = {
            "imagepath" : gcp_url,
            "timestamp": current_timestamp
        }
        self.mqtt_client.publish(message)
        print(message)
        
    #Drive towards camera for 4 seconds
    def drive_towards_camera(self):
        
        #Play sound
        print("Play alert")
        self.music.sound_play('../sounds/car-double-horn.wav')
        
        self.mqtt_client.drive_towards_camera = False
        last_msg_time = time.time() #Get start time
        timelapse = time.time() - last_msg_time
        
        
        #Turn right for 1 second
        if self.mqtt_client.cctv_camera_direction == "right":
            self.motor.right()
        elif self.mqtt_client.cctv_camera_direction == "left":
            self.motor.left()
        else:
            print(f"Invalid direction: {self.mqtt_client.cctv_camera_direction}")
        
        self.motor.forward()
        while timelapse < 1.3 :
            timelapse = time.time() - last_msg_time #Check time elapsed
            print("Turning towards camera direction: ", self.mqtt_client.cctv_camera_direction)
            sleep(0.1) #Try if sleep helps

        
        #Set motor straight and drive forward
        self.motor.straight()
        self.motor.forward()
        
        while timelapse < 5.5 :
            timelapse = time.time() - last_msg_time #Check time elapsed
            if(self.get_cam_zone() == "urn:ngsi-ld:Camera:Camera001"):
                print("Entered Cam Zone")
                break
            print("drive towards camera")
            sleep(0.1) #Try if sleep helps
            
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

    def change_mode_mqtt(self):
        json_data = {"instruction":"mqtt"}
        json_object = json.dumps(json_data)
        self.write_file(JSON_FILE_PATH,str(json_object) )

        
    def check_color_is_white(self):
        current_grayscale_value = self.px.get_grayscale_data()
        return all(list(map(lambda x: x > 120, current_grayscale_value)))
    
    #Hardware testing functions - Only to be used to check if motors are working fine
    def camera_nod(self): 
        print("Nod")
        self.px.set_cam_tilt_angle(25)
        sleep(2)
        self.px.set_cam_tilt_angle(-25)
        sleep(2)
        self.px.set_cam_tilt_angle(0)
    #Hardware testing functions
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
