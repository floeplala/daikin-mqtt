#!/usr/bin/env python3

# Daikin2mqtt.py
# JK
# version 1.2 / mei 2020
# this program collects data from the wifi-module, and sends the result as mqtt-messages
# also, it can control the airco by receiving mqtt-messages and sending them to the wif-module
# schematic:
#               ------------------------------------
#               |                                  |
#   network --- | <--> send/receive mqtt-messages  |
#               | <--> html to/from wifi-module    |
#               |                                  |
#               ------------------------------------
#




# dit programmaatje vraagt elke zoveel seconden (instelbaar) gegevens op van de Daikin wifi-module
# en stuurt deze als mqtt-bericht weer het netwerk op
# andersom werkt ook: je kunt mqtt-berichten versturen naar de module, bijvoorbeeld om de airco in- en uit te schakelen

import paho.mqtt.client as mqtt
import datetime
import time
import urllib.request 
import sys # voor regelnummer van de error

# preferences/settings
loglevel = 3                          # (loglevels: 0=OFF, 1=ERROR, 2=INFO, 3=DEBUG
logfile = "/home/pi/daikin2mqtt.log"  # set desired loglevel and logfilename
mqttname = "daikin"                   # devicename for identification used by the mqtt-broker (useful when you have more than one)
ipwifimodule = "192.168.2.40"         # ip-address of the wifi-module
looptime = 60                         # pause between loops in seconds

def LogPrint(level, text):
	# print logline to file
	if level <= loglevel:
		# add date and time
		date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
		error = ["OFF","ERROR","INFO","DEBUG"][level]
		logtext = date + " " + error + ": " + text
		print(logtext)
		filelog = open(logfile, "a")	
		filelog.write(logtext + "\n")
		filelog.close()


def on_connect(mqttc, obj, flags, rc):
	global MqttConnected
	MqttConnected = 1
	LogPrint(2, "Succesfully connected to the mqtt-broker")
	LogPrint(3, "MQTT connected, rc=" + str(rc))


def on_disconnect(mqttc, obj, rc):
	global MqttConnected
	MqttConnected = 0
	LogPrint(1, "Disconnected from the mqtt-broker")
	LogPrint(3, "MQTT disconnected, rc=" + str(rc))


def on_message(mqttc, obj, msg):
	# processing of the received mqtt-messages
	try:
		datestring = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
		msg.payload = msg.payload.decode("utf-8")
		topic = msg.topic.lower()[(len(mqttname)+1):] # convert to lower string and strip devicename
		message = str(msg.payload).lower()
		LogPrint(3, "Mqtt received topic: '" + topic + "'")
		LogPrint(3, "Mqtt received message: '" + str(msg.payload) + "'")
		if topic == "set/getinfo":
			# we are sending all data every loop, but when you are in a hurry, you can do a manual request, to have it sent right away
			LogPrint(3, "Start processing request: getinfo")
			DoLoop()
			LogPrint(3, "End processing request: getinfo")
		elif topic == "set/pow":
			LogPrint(3, "Start processing request: pow=" + message)
			# unfortunately, we cannot just say: ?pow=1, we have to supply some other mandatory parameters as well
			pow = ["0","1"][(message == "1" or message == "on" or message == "aan" or message == "true")] # we're so flexible
			DaikinCollect() # update data first, to make sure we push the most recent values back to the wifi-module
			SetDaikinData(pow, params['mode'], params['stemp'], params['f_rate'], params['f_dir'])
			LogPrint(3, "End processing request: pow=" + message)
		elif topic == "set/mode":     # mode instellen: auto, koelen, verwarmen, ventileren, drogen
			LogPrint(3, "Start processing request: mode=" + message)
			DaikinCollect() # update data first, to make sure we push the most recent values back to the wifi-module
			mode = message
			# modes:
			# 0 - Auto (currently cooling)
			# 1 - ?
			# 2 - Dry
			# 3 - Cool
			# 4 - Heat
			# 5 - ?
			# 6 - Fan
			# 7 - Auto (currently heating)
			if mode == "0" or mode == "7": # on switching to mode auto, we restore the most recent settings for that mode
				stemp = params['dt1'] # mode 1 and 7 seem to hold the same content
				f_rate = params['dfr1']
				f_dir = params['dfd1']
				validmode = True
			elif mode == "2": # on switching to mode dry
				stemp = params['dt2'] 
				f_rate = params['dfr2']
				f_dir = params['dfd2']
				validmode = True
			elif mode == "3": # on switching to mode cool
				stemp = params['dt3'] 
				f_rate = params['dfr3']
				f_dir = params['dfd3']
				validmode = True
			elif mode == "4": # on switching to mode heat 
				stemp = params['dt4'] # 4 and 5 seem to hold the same content
				f_rate = params['dfr4']
				f_dir = params['dfd4']
				validmode = True
			elif mode == "6": # on switching to mode fan
				stemp = "--"
				f_rate = params['dfr6']
				f_dir = params['dfd6']
			else:
				# no valid mode found
				validmode = False
			if validmode:
				SetDaikinData(params['pow'], mode, stemp, f_rate, f_dir)
			else:
				LogPrint(1, "Given mode '" + mode + "' is invalid")
			LogPrint(3, "End processing request: mode=" + message)
		elif topic == "set/stemp":  # instellen doeltemperatuur
			LogPrint(3, "Start processing request: stemp=" + message)
			DaikinCollect() # update data first, to make sure we push the most recent values back to the wifi-module
			stemp = message
			SetDaikinData(params['pow'], params['mode'], stemp, params['f_rate'], params['f_dir'])
			LogPrint(3, "End processing request: stemp=" + message)
	except Exception as e: 
		LogPrint(1, "Error in on_message on line " + format(sys.exc_info()[-1].tb_lineno) + ", error: " + str(e))


def on_subscribe(mqttc, obj, mid, granted_qos):
	LogPrint(2, "Subscribed to: " + str(mid) + " " + str(obj) + " " + str(granted_qos))


def MqttSend(topic, message):
	mqttc.publish(mqttname + "/" + topic, message)
	LogPrint(2, "Published " + mqttname + "/" + topic + "=" + message)


def MqttConnectAndSubscribe():
	# connect to the mqtt-broker en subscribe to the given channels
	# when calling this routing, the connection as well as the subscriptions are checked, and problems resolved when necessary
	global MqttConnected
	global MqttChannels
	global MqttSubscribed
	LogPrint(3, "Start MqttConnectAndSubscribe")
	if MqttConnected == 0: # we lost connection to the broker, try to reconnect
		try:
			mqttc.connect("localhost", 1883, 60)
			LogPrint(2, "Succesfully connected to the MQTT-broker")
		except:
			LogPrint(1, "Error while connecting to the mqtt-broker")
	if MqttConnected == 1: # we're connected (again), but are the subsciptions oke?
		for x in range(len(MqttChannels)): # check every channel
			LogPrint(3, "Checking channel " + str(x) + " (" + MqttChannels[x] + ")")
			LogPrint(3, "IsSubscribed: " + str(MqttSubscribed[x]))
			if MqttSubscribed[x] == 0: # not subscribed to this channel
				LogPrint(3, "Not subscribed to channel: " + str(x))
				try:
					r = mqttc.subscribe(MqttChannels[x], 0)
					if r[0] == 0:
						MqttSubscribed[x] = 1
						LogPrint(2, "Succesfully subscribed to channel " + MqttChannels[x])
					else:
						LogPrint(1, "Error (by client) while subscribing to channel " + MqttChannels[x])
				except:
					LogPrint(1, "Unexpected error while subscribing to channel " + MqttChannels[x])
			else:
				LogPrint(3, "We are already subscribed to channel " + str(x))
	LogPrint(3, "End MqttConnectAndSubscribe")


def DaikinCollect():
	# collect all data from Daikin wifi module and store it in a dictionary
	global params
	LogPrint(3, "Start DaikinCollect")
	try:
		# read both sensor-info and control-info from the wifi-module
		response = urllib.request.urlopen("http://" + ipwifimodule + "/aircon/get_sensor_info")
		html_s = str(response.read())
		response = urllib.request.urlopen("http://" + ipwifimodule + "/aircon/get_control_info")
		html_c = str(response.read())
	except Exception as e: 
		LogPrint(1, "Error while reading from wifi-module: " + str(e))
	LogPrint(3, "Reading from wifi-module succeeded")
	if html_s.startswith("b'ret=OK,") and html_c.startswith("b'ret=OK,"):
		text = html_s[2:] + "," + html_c[2:]
		text = text.replace("'","") # strip some quotes
		# convert to dictionary
		text = text.replace("=","':'")
		text = text.replace(",","','")
		text = "{'" + text + "'}"
		params = eval(text)
		LogPrint(3, "Parameters refreshed: " + text)
	else:
		LogPrint(1, "Unexpected result received, parameters not refreshed")
	LogPrint(3, "End DaikinCollect")
	return


def SetDaikinData(pow, mode, stemp, f_rate, f_dir):
	LogPrint(3, "Start SetDaikinData")
	try:
		param = "pow=" + pow + "&mode=" + mode + "&stemp=" + stemp + "&shum=AUTO&f_rate=" + f_rate + "&f_dir=" + f_dir
		LogPrint(3, "About to send parameters: " + param)
		response = urllib.request.urlopen("http://" + ipwifimodule + "/aircon/set_control_info?" + param)
		LogPrint(3, "Controls succesfully set")
	except Exception as e: 
		LogPrint(1, "Error setting controls, error: " + str(e))
	LogPrint(3, "End SetDaikinData")


def DoLoop():
	global MqttConnected 
	global params
	try:
		LogPrint(3, "Start DoLoop")
		MqttConnectAndSubscribe() # are we connected and subscribed? if no then fix
		DaikinCollect() # collect/update values from wifi-module
		MqttSend("status/otemp", params['otemp'])
		MqttSend("status/htemp", params['htemp'])
		MqttSend("status/cmpfreq", params['cmpfreq'])
		MqttSend("status/stemp", params['stemp'])
		MqttSend("status/powtext", ["Uit","Aan"][(params['pow']=="1")])
		#MqttSend("status/powtext", ["Off","On"][(params['pow']=="1")])
		mode = params['mode']
		modetext = ["Auto (koeling)","1?","Drogen","Koeling","Verwarming","5?","Ventilator","Auto (verwarming)"][int(mode)]
		#modetext = ["Auto (cool)","1?","Dry","Cool","Heat","5?","Fan","Auto (heat)"][int(mode)]
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


###########
#  start  #
###########

MqttConnected = 0 # flag to tell if we're connected to the broker
MqttChannels = [mqttname + "/set/#"]  # we would like to subscribe to this channel (these channels)
MqttSubscribed = [0] * len(MqttChannels) # list that hold subscription-flags (are we subscribed to this channel or not)
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
mqttc.on_subscribe = on_subscribe
MqttConnectAndSubscribe()
mqttc.loop_start() # create a thread to process incoming mqtt-messages

start = 0
while True:
	now = time.time()
	if now > start + looptime:
		DoLoop()
		start = time.time()
	time.sleep(1) # give cpu-space to other processes