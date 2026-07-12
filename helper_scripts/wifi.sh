#!/bin/bash

# script to fix ethernet issue
# (see WIFI.txt)

PASSWORD='car1'

echo "$PASSWORD" | sudo ip addr flush dev eth0
sudo ip addr add 192.168.0.11/24 dev eth0
sudo ip link set eth0 up
