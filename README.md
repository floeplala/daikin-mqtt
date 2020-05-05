# daikin-mqtt
Python script that handles the communication between MQTT and a Daikin airconditioner

I recommend to run this script as a service, for instance on a Raspberry Pi, see below for instructions.

When running, the script will connect to the given mqtt-broker. Next, it will query the wifi-module of the Daikin airconditioner to collect data. The collected data will subsequently be sent as mqtt-messages. It will automatically reconnect en resubscribe if necessary.

### Daikin --> MQTT: The following information is collected and sent over mqtt:
```
<devicename>/status/otemp           outside temperature
<devicename>/status/htemp           inside temperature (htemp probably means home-temperature)
<devicename>/status/cmpfreq         compressorfrequency
<devicename>/status/stemp           set temperature (Sollwert)
<devicename>/status/powtext         power (given as text instead of boolean): On of Off
<devicename>/status/modetext        mode (given as text instead of integer): Auto, Cool, Heat, Dry, Fan
<devicename>/graph/cool-cmpfreq		used to draw a graph in Node-RED to show the use of the airconditioner
<devicename>/graph/heat-cmpfreq		used to draw a graph in Node-RED to show the use of the airconditioner
```

### MQTT --> Daikin: The following mqtt-topics are recognized and sent to the wifi-module:
```
<devicename>/set/getinfo    when sent, the script will directly collect and send data, instead of waiting for the next cycle
<devicename>/set/pow        to switch it on and off
<devicename>/set/mode       to set the mode: 0-7 for Auto, Cool, Heat, Dry & Fan
<devicename>/set/stemp      to set the desired temperature
```

### possible future enhancements:
support for multiple airconditioners (although i have only one myself) 
support for fan speed and fan direction (i have no need for setting this through mqtt)
support for retained messages

### mode

To set the mode of the airconditioner, just pick one of these values:
```
0 = Auto
2 = Dry, 
3 = Cool
4 = Heat
6 = Fan
```
example: `mosquitto_pub -t "daikin/set/mode" -m "0"`

Reading of the mode is a litte bit different, but the script will convert the given value to a convenient text, have a look inside the script if you like to know more details about this, or if you would like to change te language.

# install as a service

