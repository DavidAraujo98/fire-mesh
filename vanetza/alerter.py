import paho.mqtt.client as mqtt

import subprocess as sub
import time
import json

lost_id = None
lost_gps={}

# Continously read the sensormesh log file
def oberveLog():
    sensors = {}
    p = sub.Popen(('sudo', 'tail', '-f', '~/.sensormesh/sensormesh.log'), stdout=sub.PIPE)
    for row in iter(p.stdout.readline,b''):
        line = json.loads(str(row.rstrip()))
    
        # Update last seen time of a stationID
        sensors[line["message"]["stationID"]] = time.time()
    
        for stationID, lastSeen in sensors.items():
            if time.time() - lastSeen > 60:
                #-------- DENM ---------
                with open("examples/in_denm.json") as f:
                    denm = json.load(f)
                # Define the station ID
                denm["originatingStationID"] = stationID
                denm["sequenceNumber"] = lost_id
                # Define the GPS coordinates
                denm["longitude"] = lost_gps[1]
                denm["latitude"] = lost_gps[0]
                # Define the speed
                denm["speed"] = 4.16  # m/s = 15 km/h
                client.publish("vanetza/in/denm", json.dumps(denm))
            
if __name__ == "__main__":
    #ip_obus = ["192.168.98.10", "192.168.98.20", "192.168.98.30", "192.168.98.40", "192.168.98.50"]
    ip_obus = ["192.168.6.130","192.168.6.140","192.168.6.149"]
    #ip_obus = ["192.168.1.109","192.168.1.110","192.168.1.111"]
    clients = []
    ids = [130,140,149]

    for i in ip_obus:
        client = mqtt.Client()
        client.connect(i, 1883, 60)
        clients.append(client)

    for client in clients:
        client.loop_start()
        
    oberveLog()