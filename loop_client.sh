#sudo -H pip install requestsl sudo -H pip install boto3; sudo -H pip install Adafruit_ADS1x15; sudo -H pip install yoctopuce

#!/bin/bash
until sudo python /home/pi/DTX1/client.py; do
    echo "Client crashed, respawning..." >&2
    sleep 1
done