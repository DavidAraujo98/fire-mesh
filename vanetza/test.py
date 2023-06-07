import paho.mqtt.client as mqtt
import json
import time
import threading
import random
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

color_obus = "blue"

# Set up Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Store the latest GPS coordinates
latest_coordinates = {}
lost_id = None
lost_gps={}
id_denm = None

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("vanetza/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global color_obus
    global lost_gps
    global lost_id
    global id_denm
    if msg.topic == "vanetza/in/cam":
        data = json.loads(msg.payload)
        index = data["stationID"]
        if index == id_denm:
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "purple"  # Purple sending denm
            }
        elif index == 0:
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "red"  # Base
            }
        elif color_obus == "blue":  #default non base is blue
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "blue"  # default
            }
        elif color_obus == "yellow":
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "yellow"  # smtg
            }
        elif color_obus == "orange":
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "orange"  # smtg
            }
        elif color_obus == "purple":
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "purple"  # smtg
            }
        else:
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "blue"  # default
            }
        # Send the latest coordinates through WebSocket
        socketio.emit("coordinates", latest_coordinates)
    #elif msg.topic == "vanetza/in/denm":           #Tive de comentar isto para ser correto com o objetivo das denm
    #    data = json.loads(msg.payload)
    #    index = data["originatingStationID"]
        # latest_coordinates[index] = {
        #     "latitude": data["latitude"],
        #     "longitude": data["longitude"],
        #     "color": "purple"  # purple = sending denms
        # }
        # # Send the latest coordinates through WebSocket
        # socketio.emit("coordinates", latest_coordinates)
    elif msg.topic == "vanetza/alert":
        data = json.loads(msg.payload)
        index = data["index"]
        latest_coordinates[index] = {
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "color": "black"            # Black = dead/lost
        }
        #Update global variables to save the values
        lost_id = data["index"]
        lost_gps = (data["latitude"],data["longitude"])
        # Send the latest coordinates through WebSocket
        socketio.emit("coordinates", latest_coordinates)

# The callback for when a client disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection.")
    else:
        index = ids.index(client._client_id)
        print("Oh no, node "+ str(index)+" went down!")

# Array with 0 initialized
index_counter = [0, 0, 0, 0, 0]
line_save = [0, 0, 0, 0, 0]

def gps_iterate(client, index):
    # setup
    global index_counter
    global line_save
    with open(f"gps/{index}.csv") as f:
        coords = f.readlines()
    # Retrieve the current line from the stored state or restart the count
    current_line = line_save[index]
    if current_line >= len(coords):
        current_line = 0
        line_save[index] = 0
        print("Restarted the file for index: " + str(index))
        print(time.ctime())
    ## "Main" part
    line = coords[current_line]
    latitude, longitude = line.strip().split(",")  # Assuming each line has format "latitude,longitude"
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

def lostInCombat(client, index):
    # setup
    global index_counter
    global line_save
    global lost_gps
    global lost_id
    with open(f"gps/{index}.csv") as f:
        coords = f.readlines()
    # Retrieve the current line from the stored state or restart the count
    current_line = line_save[index]
    if current_line >= len(coords):
        current_line = 0
        line_save[index] = 0
        print("Restarted the file for index: " + str(index))
        print(time.ctime())
    ## "Main" part
    line = coords[current_line]
    latitude, longitude = line.strip().split(",")  # Assuming each line has format "longitude,latitude"
    #-------- DENM ---------
    with open("examples/in_denm.json") as f:
        denm = json.load(f)
    # Define the station ID
    denm["originatingStationID"] = index
    denm["sequenceNumber"] = lost_id
    # Define the GPS coordinates
    denm["longitude"] = lost_gps[1]
    denm["latitude"] = lost_gps[0]
    # Define the speed
    denm["speed"] = 4.16  # m/s = 15 km/h
    client.publish("vanetza/in/denm", json.dumps(denm))
    #-------- CAM ---------
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

# Route to serve the map page
@app.route("/")
def map_page():
    return render_template("map.html")

# SocketIO event handler
@socketio.on("connect")
def handle_connect():
    # Send the latest coordinates when a client connects
    socketio.emit("coordinates", latest_coordinates)
    # Send the initial marker color when a client connects
    emit("update_color", {"color": color_obus})

@socketio.on("color_change")
def handle_color_change(data):
    color = data["color"]
    emit("update_color", {"color": color})  # Emit update_color event

def publish_coordinates():
    global color_obus
    global lost_id
    global id_denm
    
    while True:
        if lost_id != None:
            id_denm = 0
        if id_denm == lost_id:
            id_denm = 1
        for index, client in enumerate(clients):
            if(index == 1):     #swap gps file, only changes front-end
                    index = 3
            
            if index != id_denm:
                gps_iterate(client, index)
            else:
                lostInCombat(client, index)
        time.sleep(0.1)



if __name__ == "__main__":
    #ip_obus = ["192.168.98.10", "192.168.98.20", "192.168.98.30", "192.168.98.40", "192.168.98.50"]
    #ip_obus = ["192.168.6.130","192.168.6.140","192.168.6.149"]
    ip_obus = ["192.168.1.109","192.168.1.110","192.168.1.111"]
    clients = []
    ids = [130,140,149]

    for i in ip_obus:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        client.connect(i, 1883, 60)
        #ids.append(client._client_id)
        clients.append(client)

    for client in clients:
        client.loop_start()

    # Start the MQTT publishing in a separate thread
    publishing_thread = threading.Thread(target=publish_coordinates)
    publishing_thread.start()

    # Start the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000)
