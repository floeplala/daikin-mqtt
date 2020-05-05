## Daikin-MQTT interface
Python script that handles the communication between MQTT and a Daikin airconditioner

I recommend to run this script as a service, for instance on a Raspberry Pi, see below for instructions.

When running, the script will connect to the given mqtt-broker. Next, it will query the wifi-module of the Daikin airconditioner to collect data. The collected data will subsequently be sent as mqtt-messages. It will automatically reconnect and resubscribe if necessary.

### Daikin --> MQTT
The following information is collected from the wifi-module and sent over mqtt:
```
<devicename>/status/otemp           outside temperature
<devicename>/status/htemp           inside temperature (htemp probably means home-temperature)
<devicename>/status/cmpfreq         compressor frequency (an indication of the workload)
<devicename>/status/stemp           set temperature (Sollwert)
<devicename>/status/powtext         power (given as text instead of boolean): On, Off
<devicename>/status/modetext        mode (given as text instead of integer): Auto, Cool, Heat, Dry, Fan
<devicename>/graph/cool-cmpfreq     used to draw a graph in Node-RED to show the use of the airconditioner
<devicename>/graph/heat-cmpfreq     used to draw a graph in Node-RED to show the use of the airconditioner
```

### MQTT --> Daikin
The following mqtt-topics are recognized and sent to the wifi-module:
```
<devicename>/set/getinfo    when sent, the script will directly collect and send data, instead of waiting for the next cycle
<devicename>/set/pow        to switch it on and off
<devicename>/set/mode       to set the mode: 0-7 for Auto, Cool, Heat, Dry & Fan (see below for details)
<devicename>/set/stemp      to set the desired temperature
```

### Mode
To set the mode of the airconditioner, just pick one of these values:
```
0 = Auto
2 = Dry
3 = Cool
4 = Heat
6 = Fan
Example: mosquitto_pub -t "daikin/set/mode" -m "0" to switch to auto-mode
```
When the airconditioner is in Auto-mode, it will return a 0 when it is currently cooling, and a 7 when it is currently heating. I don't know the purpose of mode 1 and 5. If you do, please let me know.

### Install as a Service (on a Pi)
The best way I found to run a python-script as a service on a Raspberry Pi is explained here:
https://timleland.com/how-to-run-a-linux-program-on-startup/

### Wishlist:
- Support for multiple airconditioners (although I have only one myself) 
- Support for fan speed and fan direction (I have no need for setting this through mqtt)
- Support for retained messages
- More knowledge of the modes: the purpose of mode 1 and 5?

