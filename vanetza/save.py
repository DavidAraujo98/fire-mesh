import random
import paho.mqtt.client as mqtt
import json
import time
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO

# Set up Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Store the latest GPS coordinates
latest_coordinates = {}

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("vanetza/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    
    if(msg.topic!="vanetza/in/denm"):
        pass
    else:
        data = json.loads(msg.payload)
        index = data["stationID"]
        latest_coordinates[index] = {
            "latitude": data["latitude"],
            "longitude": data["longitude"]
        }
        # Send the latest coordinates through WebSocket
        socketio.emit("coordinates", latest_coordinates)
        print(msg.topic+" "+str(msg.payload))

# The callback for when a client disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")
    else:
        index=ids.index(client._client_id)
        print("Oh no, node "+ str(index)+" went down!")


# Array with 0 initialized
index_counter = [0,0,0,0,0]
line_save = [0,0,0,0,0]

#Function that generates CAMs with correct GPS
def gps_iterate(client, index):
    #setup
    global index_counter
    global line_save
    # index = ids.index(client._client_id)
    with open(f"gps/{index}.csv") as f:
        coords = f.readlines()
    # Retrieve the current line from the stored state or restart the count
    current_line = line_save[index]
    if current_line >= len(coords):
        current_line = 0
        line_save[index]=0
        print("Restarted the file for index: "+ str(index))
        print(time.ctime())
    ## "Main" part
    line = coords[current_line]
    longitude, latitude = line.strip().split(",")  # Assuming each line has format "longitude,latitude"
    with open("in_cam.json") as cam_file:
        cam = json.load(cam_file)
    # Define the station ID
    cam["stationID"] = index
    # Define the GPS coordinates
    cam["longitude"] = float(longitude)
    cam["latitude"] = float(latitude)
    # Define the speed
    cam["speed"] = 4.16  # m/s = 15 km/h
    client.publish("vanetza/in/cam", json.dumps(cam))
    # Increment the current line for the next iteration
    if index_counter[index] == 9:
        line_save[index] = current_line + 1
        index_counter[index] = 0
    else:
        index_counter[index] = index_counter[index] + 1  
    f.close()

def lostInCombat(client):
    index=ids.index(client._client_id)
    with open ("examples/in_denm.json") as f:
            denm = json.load(f)
    denm["originatingStationID"]=index
    denm["longitude"] = random.uniform(-7.736327469013476,-7.726778805428308)
    denm["latitude"] = random.uniform(40.311505466924444,40.31729747250064)
    client.publish("vanetza/in/denm",json.dumps(denm))
    f.close()


#--------------------------- WEB --------------------------------

# Route to serve the map page
@app.route("/")
def map_page():
    return render_template("map.html")

# SocketIO event handler
@socketio.on("connect")
def handle_connect():
    # Send the latest coordinates when a client connects
    socketio.emit("coordinates", latest_coordinates)

if __name__ == "__main__":
    # Start the Flask app with SocketIO
    socketio.run(app)

#-------------------------------------------------------------"MAIN"------------------------------------

ip_obus = ["192.168.98.10","192.168.98.20","192.168.98.30","192.168.98.40","192.168.98.50"]
clients = []
threads= []
ids = []

for i in ip_obus:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.connect(i, 1883, 60)
    ids.append(client._client_id)
    clients.append(client)

for c in clients:
    thread = threading.Thread(target=c.loop_forever)
    thread.start()
    threads.append(thread)

#client.loop_forever()
print(time.ctime())
while(1):
    for index, c in enumerate(clients):
        gps_iterate(c, index)
    time.sleep(0.1)
    # cont+=1
    # if (cont%100 == 0):
    #     cont=0
    #     clients[0].disconnect()
    #     lostInCombat(clients[1])


