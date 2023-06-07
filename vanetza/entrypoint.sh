#!/bin/sh

### SensorMesh adaptation ###
# Update IPFS_PATH
export IPFS_PATH="$HOME/.ipfs" >> ~/.bashrc
bash
# Consume call paremeters
REPO_NAME=$1        #FIRESTATION_ID:VEHICLE_NAME
EVENT_ID=$2         #Iditifier of the current event
INTF_NAME=$3        #Names of the used network interface
SWARM_KEY=$4        #Private IPFS Swarm key
STORE=$5            #OrbitDB database store address (name if first vehicle)
# Initiate node and clean swarm
ipfs init
# Initiate sensormesh
sensormesh init --nodename=$REPO_NAME --swarmkey=$SWARM_KEY
# Subscribe to MQTT channel 
sensormesh channel connect --brokerUrl="tcp://127.0.0.1:1883" --topic="vanetza/in/cam"
# Remove bootstrap addresses
ipfs bootstrap rm --all
# Change the routing type to Distributed Hash Table
ipfs config Routing.Type dht
# Starting IPFS daemon service and gives it time to initialize
ipfs daemon --enable-pubsub-experiment &
sleep 5
# Starting the sensormesh daemon
sensormesh daemon --storeaddress=$STORE
### SensorMesh adaptation ###


IP_ADDR=$(ip -f inet addr show eth0 | awk '/inet / {print $2}')
GW_ADDR=$(ip r | awk '/default / {print $3}')
BR_ID=br0

if [ $SUPPORT_MAC_BLOCKING = true ] ; then
    brctl addbr $BR_ID
    ip a a $IP_ADDR dev $BR_ID
    ip a d  $IP_ADDR dev eth0
    brctl addif $BR_ID eth0
    ip link set $BR_ID up
    ip r a default via $GW_ADDR
fi

printf '#!/bin/sh\nebtables -A INPUT -s $1 -j DROP;' > /bin/block
printf '#!/bin/sh\nebtables -D INPUT -s $1 -j DROP;' > /bin/unblock
chmod +x /bin/block
chmod +x /bin/unblock

if [ $START_EMBEDDED_MOSQUITTO = true ] ; then
    printf "\nlistener ${EMBEDDED_MOSQUITTO_PORT} 0.0.0.0\nallow_anonymous true\n\n" > mosquitto.conf
    /usr/sbin/mosquitto -c mosquitto.conf &>/dev/null &
    sleep 2
fi

if [ $(uname -m) = "armv7l" ] ; then
    cd /root/go/pkg/mod/github.com/rticommunity/*/rticonnextdds-connector/lib/linux-arm/
    export LD_LIBRARY_PATH=$(pwd)
fi
if [ $(uname -m) = "aarch64" ] ; then
    cd /root/go/pkg/mod/github.com/rticommunity/*/rticonnextdds-connector/lib/linux-arm64/
    export LD_LIBRARY_PATH=$(pwd)
fi

/root/go/src/dds-vanetza-service/main /config.ini /Vanetza_DDS_Spec.xml &>/dev/null &
sleep 1
/usr/local/bin/socktap -c /config.ini