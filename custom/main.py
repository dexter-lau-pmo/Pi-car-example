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


JSON_FILE_PATH = '/home/admin/picar-x/custom/REST/data.json'
POWER = 50
SAFE_DISTANCE = 30   # > 40 safe
DANGER_DISTANCE = 20 # > 20 && < 40 turn around, 
                    # < 20 backward

class App(object):
    def __init__(self):
        self.x_coordinate = 0
        self.y_coordinate = 0
        self.mqtt_client = MQTTClient()
        self.px = Picarx()
        self.motor = Motor()
        self.auto = AutoPilot(self.px, self.motor)
        self.auto.start()
        self.is_avoiding_collision = False
        self.alert_x1 = 0.0
        self.alert_x2 = 1.0
        self.alert_y1 = 0.0
        self.alert_y2 = 1.0    
    
    # TODO: clear json file value after reading it
    def run(self):
        self.mqtt_client.connect()
        last_msg_time = time.time()
        self.mqtt_client.stop_car == True
        
        #while True: #Motor testing only
            #self.camera_nod()
            #self.camera_shake()
        self.px.set_cam_tilt_angle(25)
        
        while True:
            try:
                with open(JSON_FILE_PATH, 'r') as file:
                    fcntl.flock(file, fcntl.LOCK_SH)
                    data = json.load(file)
                    fcntl.flock(file, fcntl.LOCK_UN)
            except json.decoder.JSONDecodeError as json_err:
                continue
            insn = data['instruction'] #get current mode (manual/auto) from the JSON file loaded earlier
            self.update_bot_coordinates() #calculate the bot position
            self.update_alert_zone()#if you got a message that updates the bots alert zone, update it

            #Process special statuses
            if self.mqtt_client.drive_towards_camera == True: #If you get a message "names" from the Camera Drive forward and change to auto mode. This simulates finding the camera
                print("\n\n\nDriving to camera\n\n\n\n")
                self.drive_towards_camera()
                self.mqtt_client.drive_towards_camera = False
            
            elif self.mqtt_client.stop_car == True: #If you get a message to change car mode to stop, do so
                print("changing to stop mode")
                self.change_mode_stop()
                self.mqtt_client.stop_car = False
                
            elif self.mqtt_client.auto_car == True: # if you get a message tochange car mode to auto, do so
                print("changing to auto mode")
                self.change_mode_auto()
                self.mqtt_client.auto_car = False 


            
            if insn == "auto": #If current mode is auto , we make the robot follow people arond
                time_elapsed = time.time() - last_msg_time
                if time_elapsed >3:
                    last_msg_time = time.time()
                    self.send_mqtt_update("Auto")
                    print("Auto")
                    
                #Collision avoidance
                distance = round(self.px.ultrasonic.read(), 2)
                if distance >= SAFE_DISTANCE or distance < 0: #sensor gives -1 when it fails to receive ultrasonic feedback
                    if self.is_avoiding_collision:
                        self.motor.stop()
                        self.is_avoiding_collision = False
                    self.auto.event.set() # unpauses auto thread
                elif distance >= DANGER_DISTANCE:
                    self.auto.event.clear() # pauses the auto thread
                    self.is_avoiding_collision = True
                    self.motor.right()
                    self.motor.forward()
                    sleep(1)
                elif distance >= 0: 
                    self.auto.event.clear()
                    self.is_avoiding_collision = True
                    print("HIT")
                    self.motor.left()
                    self.motor.backward()
                    sleep(1)
                                       
            else:
                
                time_elapsed = time.time() - last_msg_time
                
                if time_elapsed >3:
                    last_msg_time = time.time()
                    self.send_mqtt_update("Manual")
            
                if insn == "forward":
                    self.auto.event.clear()
                    self.motor.forward()
                elif insn == "left":
                    self.auto.event.clear()
                    self.motor.left()
                elif insn == "right":
                    print("RIGHT")
                    self.auto.event.clear()
                    self.px.set_dir_servo_angle(35)
                elif insn == "backward":
                    self.auto.event.clear()
                    self.motor.backward()
                elif insn == "straight":
                    self.auto.event.clear()
                    self.motor.straight()
                elif insn == "stop":
                    self.auto.event.clear()
                    self.motor.stop()
                    self.motor.straight()
                    self.px.set_cam_tilt_angle(25)
                    
    def send_mqtt_update(self, mode):
        print(self.x_coordinate,self.y_coordinate)
        current_timestamp = datetime.now().isoformat() # add timestamp param
        print("\n", current_timestamp)
        
        message = {
            "x" : self.x_coordinate,
            "y" : self.y_coordinate,
            "status" : self.motor.get_status(),
            "mode" : mode,
            "camera-zone": self.get_cam_zone(),
            "timestamp": current_timestamp
        }
        self.mqtt_client.publish(message)

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
        
    def get_cam_zone(self):
        if self.check_color_is_white():# An alternate way to trigger the camera zone is for robot to run over white stuff
            print("ITS WHITE")
            return "urn:ngsi-ld:Camera:Camera001"
            
        #arbitrary dummy zone for camera where cam field is x is 1 to 10, y is 1 to 10
        if self.x_coordinate < self.alert_x2 and self.y_coordinate < self.alert_y2 and self.x_coordinate > self.alert_x1 and self.y_coordinate > self.alert_y1:
            return "urn:ngsi-ld:Camera:Camera001"
            
        else:
            return "NULL"
    
    def drive_towards_camera(self):
        last_msg_time = time.time()
        timelapse = time.time() - last_msg_time
        self.motor.straight()
        self.motor.forward()
        while timelapse < 4.5:
            timelapse = time.time() - last_msg_time
            if(self.get_cam_zone() == "urn:ngsi-ld:Camera:Camera001"):
                print("Entered Cam Zone")
                break
            print("drive towards camera")
        self.motor.stop()
        json_data = {"instruction":"auto"}
        json_object = json.dumps(json_data)
        print("Attempt to update JSON")
        self.write_file(JSON_FILE_PATH,json_object)
            
    def write_file(self, filename, fileinput):
        while True:
            print("File write attempt")
            with open(filename, "w") as file:
                fcntl.flock(file, fcntl.LOCK_SH)
                file.write(fileinput)
                fcntl.flock(file, fcntl.LOCK_UN)
                print("File write success")
                break
                            
    def change_mode_auto(self):
        json_data = {"instruction":"auto"}
        json_object = json.dumps(json_data)
        self.write_file(JSON_FILE_PATH,json_object)

    def change_mode_stop(self):
        json_data = {"instruction":"stop"}
        json_object = json.dumps(json_data)
        self.write_file(JSON_FILE_PATH,json_object)
        
    def check_color_is_white(self):
        current_grayscale_value = self.px.get_grayscale_data()
        return all(list(map(lambda x: x > 120, current_grayscale_value)))
            
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
        
if __name__ == '__main__':
    try:
        app =App()
        app.run()
    except KeyboardInterrupt:
        Motor().stop()
        pass
