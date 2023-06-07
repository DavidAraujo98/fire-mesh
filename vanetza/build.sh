#!/bin/bash

#   Usage:
##  $ ./build.sh [OPTIONS]
##
##  OPTIONS:
##      --build         - Builds a new image with the specified name
##      --up            - Starts containers using the image with the specified name

TARGET_IMAGE_NAME="firemeshnode"

if [[ $1 == "--build" ]]; then
    
    # Build golang configuration file
    cd ../ipfs/sensor-mesh
    OUT=$(go build -o ../nodes/sensormesh.o main.go)
    if [[ $OUT != "" ]]; then
        echo -e "[!] sensormesh compiling error !"
    fi
    echo -e "[+] SensorMesh binary compiled!"
    cd ../../vanetza

    # Guarantees that every shell script is in Unix format. (Usefull if you develop in Windows)
    dos2unix -q *.sh

    # Crete vanetza network
    docker network create vanetzalan0

    # Build new image
    echo -e "[*] Building docker image..."
    SHA=$(docker build -q --no-cache -t $TARGET_IMAGE_NAME -f ../ipfs/nodes/CombatVehicle.Dockerfile ../ipfs/nodes) && echo -e "[+] Docker image built. $SHA"
fi

if [[ $1 == "--up" || $2 == "--up" ]]; then
    #  These keys will be created and hand out by a third party that creates the events !!

    ## Generate Swarm key wich must be shared between all nodes
    SWARM_KEY=$(head -c 32 /dev/urandom | od -t x1 -A none - | tr -d '\n '; echo '')
    echo -e "[+] Swarm key generated: $SWARM_KEY"

    # First node creates the OrbitDB store with default name
    echo -e "[!] First vehicle on scene..."
    SWARM_KEY=$SWARM_KEY STORE=$STORE docker-compose -f docker-compose-initial.yml up -d --remove-orphans
    sleep 10

     # Search for the OrbitDB address inside first firemesh node
    STORE=$(docker exec sensormesh0 sensormesh config orbitdb.storeaddress)
    echo -e "[+] Store address created by first vehicle: $STORE"
    sleep 2

    # Spin up secondary nodes with created database address to connect to 
    echo -e "[!] Other vehicle arriving on scene..."
    SWARM_KEY=$SWARM_KEY STORE=$STORE docker-compose -f docker-compose-secondary.yml up -d
fi
