import paho.mqtt.client as mqtt
import json

class MQTTClient:
    def __init__(self):
        self.connect()
        self.x1 = 0.0
        self.x2 = 1.0
        self.y1 = 1.0
        self.y2 = 2.0
        self.drive_towards_camera = False
        self.stop_car = False
        self.auto_car = False
        
    def on_publish(self, client, userdata, mid):
        print(f"Message published: {mid}")

    def publish(self, json_object):
        print("Message published")
        self.client.publish(self.topic, json.dumps(json_object))
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            #added subscribe
            self.client.subscribe("/1234/Robot001/cmd")
            print("Subscribed to /1234/Robot001/cmd")

        else: 
            print("Failed to connect to MQTT broker")
            

        
            
    def on_message(self, client, userdata, msg):
        #print("Msg received")
        #process JSON to add coordinates, plz check code
        message_data = json.loads(msg.payload.decode())
        for key in message_data:
                if key == "x1":
                        self.x1 = float(message_data["x1"])
                if key == "y1":
                        self.y1 = float(message_data["y1"])
                if key=="x2":
                        self.x2 = float(message_data["x2"])
                if key =="y2":
                        self.y2 = float(message_data["y2"])
                if key=="names":
                        self.drive_towards_camera = True
                        print("\n\\n\n\n\n\n\nAlert Received, start driving plz\n\n\n\n\n\n")  
                if key=="stop":
                        self.stop_car = True
                        print("\nCmd Received, stop mode for car\n")                         
                if key=="auto":
                        self.auto_car = True
                        print("\nCmd Received, auto mode for car\n") 
                                        
    def connect(self):
        broker = "35.240.151.148"
        port = 1883
        self.topic = "/1234/Robot001/attrs"
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

        self.client.on_publish = self.on_publish
        self.client.on_connect = self.on_connect

        
        #added subscribe
        self.client.on_message = self.on_message
        
        self.client.connect(broker, port, 60)
        self.client.loop_start()


