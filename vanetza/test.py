import haversine as hs
import paho.mqtt.client as mqtt
import json
import time
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

color_obus = "blue"

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
    global color_obus
    if msg.topic == "vanetza/in/cam":
        data = json.loads(msg.payload)
        index = data["stationID"]
        if index == 0:
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "red"  # Add the color property to the coordinates object
            }
        elif index == 1:
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "blue"  # Add the color property to the coordinates object
            }
        elif color_obus == "blue":
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "blue"  # Add the color property to the coordinates object
            }
        elif color_obus == "yellow" and index != 2:
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "yellow"  # Add the color property to the coordinates object
            }
        else:
            latest_coordinates[index] = {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "color": "orange"  # Add the color property to the coordinates object
            }
        # Send the latest coordinates through WebSocket
        socketio.emit("coordinates", latest_coordinates)
    elif msg.topic == "vanetza/in/denm":
        data = json.loads(msg.payload)
        index = data["originatingStationID"]
        latest_coordinates[index] = {
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "color": "orange"  # Add the color property to the coordinates object
        }
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
coords_base = (40.314712104823286,-7.735168933868409)
coords_fugitivo = (40.31412308743567,-7.736080884933473)

def gps_iterate(client, index):
    # setup
    global coords_base
    global coords_fugitivo
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
    latitude, longitude = line.strip().split(",")  # Assuming each line has format "longitude,latitude"
    if index==0:
        coords_base=(float(latitude),float(longitude))
    if index==1:
        coords_fugitivo=(float(latitude),float(longitude))
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
    global coords_base
    global coords_fugitivo
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
    latitude, longitude = line.strip().split(",")  # Assuming each line has format "longitude,latitude"
    if index==0:
        coords_base=(float(latitude),float(longitude))
    if index==1:
        coords_fugitivo=(float(latitude),float(longitude))
    #DENM---------
    with open("examples/in_denm.json") as f:
        denm = json.load(f)
    # Define the station ID
    denm["originatingStationID"] = index
    # Define the GPS coordinates
    denm["longitude"] = float(longitude)
    denm["latitude"] = float(latitude)
    # Define the speed
    denm["speed"] = 4.16  # m/s = 15 km/h
    client.publish("vanetza/in/denm", json.dumps(denm))
    #CAM---------
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
    global coords_fugitivo
    c = 0
    while True:
        for index, client in enumerate(clients):
            distance = hs.haversine(coords_base,coords_fugitivo)*1000
            print("d: "+str(distance))
            if index != 2 or int(distance) < 120:
                gps_iterate(client, index)
            else:
                lostInCombat(client, index)
                color_obus = "yellow"
                socketio.emit("color_change", {"color": color_obus}, namespace="/")
                c=1
                print("lostInCombat " + str(color_obus))
            if c == 1 and distance < 120:
                c=0
                color_obus = "blue"
                socketio.emit("color_change", {"color": color_obus}, namespace="/")
        time.sleep(0.1)



if __name__ == "__main__":
    ip_obus = ["192.168.98.10", "192.168.98.20", "192.168.98.30", "192.168.98.40", "192.168.98.50"]
    clients = []
    ids = []

    for i in ip_obus:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        client.connect(i, 1883, 60)
        ids.append(client._client_id)
        clients.append(client)

    for client in clients:
        client.loop_start()

    # Start the MQTT publishing in a separate thread
    publishing_thread = threading.Thread(target=publish_coordinates)
    publishing_thread.start()

    # Start the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000)
