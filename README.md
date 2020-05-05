# daikin-mqtt
Python script that handles the communication between MQTT and a Daikin airconditioner

I recommend to run this script as a service, for instance on a Raspberry Pi, see below for instructions.

When running, the script will connect to the given mqtt-broker. Next, it will query the wifi-module of the Daikin airconditioner to collect data. The collected data will subsequently sent as mqtt-messages. It will automatically reconnect en resubscribe if necessary.

The following information is collected and sent over mqtt:
<devicename>/status/otemp           outside temperature
<devicename>/status/htemp           inside temperature (htemp probably means home-temperature)
<devicename>/status/cmpfreq         compressorfrequency
<devicename>/status/stemp           set temperature (Sollwert)
<devicename>/status/powtext         power (given as text instead of boolean): On of Off
<devicename>/status/modetext        mode (given as text instead of integer): Auto, Cool, Heat, Dry, Fan
<devicename>/graph/cool-cmpfreq		used to draw a graph in Node-RED to show the use of the airconditioner
<devicename>/graph/heat-cmpfreq		used to draw a graph in Node-RED to show the use of the airconditioner
