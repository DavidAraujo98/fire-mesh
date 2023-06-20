# FireMesh Diogo Mendes
# This python pub to vanetza/alert
# .
# DENM will be sent with pub to vanetza/alert

import paho.mqtt.client as mqtt
import json
import threading

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("vanetza/#")

def denm():
    f = open('examples/alert.json')
    m = json.load(f)
    m["index"] = 1
    m["latitude"] = 40.31323373258425
    m["longitude"] = -7.7365207493567185
    m = json.dumps(m)
    client.publish("vanetza/alert",m)
    print("Simulation: lost a unit! Sending DENM!")
    f.close()


client = mqtt.Client()
client.on_connect = on_connect
client.connect("192.168.6.130", 1883, 60)

threading.Thread(target=client.loop_forever).start()
denm()