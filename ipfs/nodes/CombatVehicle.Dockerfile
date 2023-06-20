FROM ipfs/kubo:latest

ENV VEHICLE_NAME="vfci#"
ENV FIRESTATION_ID="0000"
ENV EVENT_ID="1111"
ENV INTF_NAME="eth0"
ENV SWARM_KEY=""
ENV STORE=""
ENV VANETZA_IP="192.168.98.50"

COPY sensormesh.o /usr/local/bin/sensormesh
COPY bootstrap.sh /usr/local/bin/bootstrap.sh
COPY alert.py alert.py
COPY requirements.txt requirements.txt 

RUN chmod -R 777 /usr/local/bin/*

ENTRYPOINT bootstrap.sh ${FIRSTATION_ID}_${VEHICLE_NAME} ${EVENT_ID} ${INTF_NAME} ${SWARM_KEY} ${STORE} ${VANETZA_IP}}
