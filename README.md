# daikin-mqtt
Python script that handles the communication between MQTT and a Daikin airconditioner

I recommend to run this script as a service, for instance on a Raspberry Pi, see below for instructions.

When running, the script will connect to the given mqtt-broker. Next, it will query the wifi-module of the Daikin airconditioner to collect data. The collected data will subsequently sent as mqtt-messages. It will automatically reconnect en resubscribe if necessary.

The following information is collected and sent over mqtt:
<devicename>/status/otemp           outside temperature
<devicename>/status/htemp           inside temperature (htemp probably means home-temperature)
<devicename>/status/cmpfreq         compressorfrequency
<devicename>/status/stemp           set temperature (Sollwert)
<devicename>/status/powtext         power (stated as text instead of boolean): On of Off
MqttSend("status/modetext", modetext)
		if mode == "3" or mode == "0": # cool or auto(currently cooling)
			MqttSend("graph/cool-cmpfreq", params['cmpfreq'])
			MqttSend("graph/heat-cmpfreq", "False") # this leaves a gap in the graph, just the way we like it
		elif mode == "4" or mode == "7": # heat or auto(currently heating)
			MqttSend("graph/heat-cmpfreq", params['cmpfreq'])
			MqttSend("graph/cool-cmpfreq", "False")
		LogPrint(3, "End DoLoop")
	except Exception as e: 
		LogPrint(1, "Error in DoLoop on line " + format(sys.exc_info()[-1].tb_lineno) + ", error: " + str(e))
