import paho.mqtt.client as mqtt

# MQTT broker details
broker_address = "35.198.213.246"
port = 1883

# Callback function for when a message is received from the broker
def on_message(client, userdata, message):
    print("Received message on topic:", message.topic)
    print("Message:", str(message.payload.decode("utf-8")))

# Callback function for when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        # Subscribe to a topic
        topic = "/1234/Robot001/attrs"
        client.subscribe(topic)
    else:
        print("Failed to connect to MQTT broker")

# Create MQTT client instance
client = mqtt.Client()

# Assign callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to MQTT broker
client.connect(broker_address, port)

# Keep the client running to receive messages
client.loop_forever()
