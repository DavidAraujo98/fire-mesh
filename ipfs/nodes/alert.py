# FireMesh Diogo Mendes & David Araújo
# This python pub to vanetza/alert
# .
# DENM will be sent with pub to vanetza/alert

import subprocess as sub
import time
import paho.mqtt.client as mqtt
import json
import threading
import sys

clientAlert = mqtt.Client()


def on_connect_alert(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("vanetza/alert")


def denm(message):
    clientAlert.publish("vanetza/alert", json.dumps(message))
    print("Simulation: lost a unit! Sending DENM!")


clientAlert.on_connect = on_connect_alert
clientAlert.connect(sys.argv[1], 1883, 60)
threading.Thread(target=clientAlert.loop_forever).start()

obus = {}
p = sub.Popen("tail", "-l", "~/.sensormesh/sensormesh.log", stdout=sub.PIPE)
for row in iter(p.stdout.readline, b""):
    line = str(row.rstrip())
    cam = json.loads(line)["message"]
    now = time.time()

    for stationID in obus.keys():
        if obus.get(stationID, None):
            obu = obus[stationID]
            if now - obu["lastContact"] >=30:
                m = dict(obu)
                del m["lastContact"]
                denm(m)

    obus[cam["StationID"]] = {
        "index": cam["StationID"],
        "latitude": cam["latitude"],
        "longitude": cam["longitude"],
        "lastContact": now,
    }