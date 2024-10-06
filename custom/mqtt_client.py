import paho.mqtt.client as mqtt
import json

class MQTTClient:
    def __init__(self):
        #self.connect() #called in main.py
        self.broker_ip = "35.240.151.148"
        self.x1 = 0.0
        self.x2 = 1.0
        self.y1 = 1.0
        self.y2 = 2.0
        self.drive_towards_camera = False
        self.cctv_camera_direction = "None"
        self.stop_car = False
        self.auto_car = False
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.connected_flag=False # check if is connected
        self.servo_dir = None 
        self.motor_dir = None 
        self.override_auto_mode = None
        
    def on_publish(self, client, userdata, mid):
        print(f"Message published: {mid}")

    def publish(self, json_object):
        if (self.connected_flag):
                print("Message published")
                self.client.publish(self.topic, json.dumps(json_object))
        else:
                print("Currently disconnected, cannot publish")
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            #added subscribe
            self.client.subscribe("/1234/Robot001/cmd")
            print("Subscribed to /1234/Robot001/cmd")
            self.connected_flag=True

        else: 
            print("Failed to connect to MQTT broker")
            self.connected_flag=False
            
    def on_disconnect(self, client, userdata, rc):
        print("disconnecting reason  "  +str(rc))
        self.connected_flag=False # check if is connected
        
            
    def on_message(self, client, userdata, msg):
        #print("Msg received")
        #process JSON to add coordinates, plz check code
        message_data = json.loads(msg.payload.decode())
        for key in message_data:
                if key == "x1":
                        self.x1 = float(message_data["x1"])
                if key == "y1": #Servo control
                        #self.y1 = float(message_data["y1"]) #Use for servo control?
                        self.servo_dir = message_data["y1"]
                        print("y1  ", message_data["y1"])
                        
                        if message_data["y1"] == "auto":
                                self.auto_car = True #Flag will trigger entering auto mode
                        elif message_data["y1"] == "left" or message_data["y1"] == "right" or message_data["y1"] == "up" or message_data["y1"] == "down" or message_data["y1"] == "reset" or message_data["y1"] == "snapshot":
                                self.override_auto_mode = True #Flag will prompt exit of auto mode. Triggered when valid

                        
                if key=="x2":
                        self.x2 = float(message_data["x2"])
                        
                if key =="y2": #Motor control
                        #self.y2 = float(message_data["y2"]) #Use for motor control?
                        #auto, forwards, backward, etc
                        self.motor_dir = message_data["y2"]
                        print("y2  ", message_data["y2"])
                        
                        if message_data["y2"] == "auto":
                                self.auto_car = True #Flag will trigger entering auto mode
                        elif message_data["y2"] == "left" or message_data["y2"] == "right" or message_data["y2"] == "forward" or message_data["y2"] == "backward" or message_data["y2"] == "stop" or message_data["y2"] == "snapshot":
                                self.override_auto_mode = True #Flag will prompt exit of auto mode. Triggered when valid
                        
                #Names sends camera name, and triggers car to drive forward and enter auto mode
                if key=="names":
                        self.drive_towards_camera = True
                        print("\n\\n\n\n\n\n\nAlert Received \n\n\n\n\n\n")  
                        
                        #Check for Camera name in payload
                        if "Camera002" in message_data["names"]:
                                print("Message from Camera 2, turn left")
                                self.cctv_camera_direction = "left"
                        if "Camera001" in message_data["names"]:
                                self.cctv_camera_direction = "left"
                                print("Message from Camera 1, turn right")
                                self.cctv_camera_direction = "right"
                        
                if key=="stop":
                        self.stop_car = True
                        print("\nCmd Received, stop mode for car\n")                         
                if key=="auto":
                        self.auto_car = True
                        print("\nCmd Received, auto mode for car\n") 
                                        
    def connect(self):
        broker = self.broker_ip
        port = 1883
        self.topic = "/1234/Robot001/attrs"
        
        self.client.on_publish = self.on_publish
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        #added subscribe
        self.client.on_message = self.on_message
        
        #Attempt to connect if connection does not exist
        if self.connected_flag == False:
                try:
                    self.client.connect(broker, port, 60) #Try to connect
                except:
                    print("Connection failed") #Handle if failed

        self.client.loop_start()


