#!/bin/bash

# Find all devices on the LAN
arp-scan --localnet > localnet.txt

# Install nmap if not installed
if [ -e $(which nmap) ]
then 
	echo -e "\nNmap is installed"
else
	echo "Installing nmap using brew (please install brew if you haven't."
	echo "Passowrd may be required."
	brew install nmap
fi

# Cut out lines that aren't devices
grep 192.168 localnet.txt > results.txt

# Iterate through all devices
while read line
do
	mac=$(echo $line | awk -F " " '{print $2}')

	# Turbine 1's MAC address
	if [ "$mac" == "b8:27:eb:4e:f2:b6" ]
	then
		echo -e "\nMapping turbine 1"
		ip=$(echo $line | awk -F " " '{print $1}')
		echo "turbine ip is $ip"
		echo "Turbine1 $ip $(nmap -p 22 $ip -Pn | grep ssh | awk -F " " '{print $2}')"
	fi

	# Turbine 2's MAC address
	if [ "$mac" == "b8:27:eb:24:a6:a1" ]
	then
		echo -e "\nMapping turbine 2"
		ip=$(echo $line | awk -F " " '{print $1}')
		echo "turbine ip is $ip"
		echo "Turbine2 $ip $(nmap -p 22 $ip -Pn | grep ssh | awk -F " " '{print $2}')"
	fi

	# Turbine 3's MAC address
	if [ "$mac" == "b8:27:eb:63:bc:2c" ]
	then
		echo -e "\nMapping turbine 3"
		ip=$(echo $line | awk -F " " '{print $1}')
		echo "turbine ip is $ip"
		echo "Turbine3 $ip $(nmap -p 22 $ip -Pn | grep ssh | awk -F " " '{print $2}')"
	fi

done < results.txt

# Cleanup
echo ""
rm results.txt localnet.txt