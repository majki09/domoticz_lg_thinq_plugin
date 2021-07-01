#!/usr/bin/python3

# Python Plugin LG ThinQ API v2 integration.
#
# Author: majki
#
"""
<plugin key="LG_ThinQ" name="LG ThinQ" author="majki" version="1.0.0" externallink="https://github.com/majki09/domoticz_lg_thinq_plugin">
    <description>
        <h2>LG ThinQ domoticz plugin</h2><br/>
        Plugin uses LG API v2. All API interface (with some mods) comes from  <a href="https://github.com/tinkerborg/thinq2-python">github.com/tinkerborg/thinq2-python</a>.<br/><br/>
        If you have LG devices that doesn't work with API v1 (wideq plugin), maybe this one will be a chance for you.<br/><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Reading unit parameters from LG API</li>
            <li><del>Control unit with LG API</del></li>
        </ul>
        <h3>Compatible devices</h3>
        <ul style="list-style-type:square">
            <li>AC - Air Conditioning (tested with LG PC12SQ unit).</li>
        </ul>
        <br/>
    </description>
    <params>
        <param field="Address" label="MQTT broker IP Address" width="100px" required="true" default="test.mosquitto.org"/>
        <param field="Port" label="MQTT Connection" required="true" width="100px">
            <options>
                <option label="Unencrypted" value="1883" default="true" />
                <option label="Encrypted" value="8883" />
                <option label="Encrypted (Client Certificate)" value="8884" />
            </options>
        </param>
        <param field="Username" label="MQTT broker Username" width="100px"/>
        <param field="Password" label="MQTT broker Password" width="100px"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
            </options>
        </param>
        <param field="Mode1" label="Device type" width="100px">
            <options>
                <option label="AC" value="type_ac" default="true" />
            </options>
        </param>
        <param field="Mode2" label="Device ID" width="250px"/>
    </params>
</plugin>
"""
import Domoticz
#from Domoticz import Devices, Parameters
import json
import random


# class LGDevice:
    # def __init__(self):


class BasePlugin:
    enabled = False
    mqttConn = None
    counter = 0
    
    mqtt_topic = "lg_thinq"
    # lg_device = LGDevice()
    
    def __init__(self):
        # return
        self.device_id = ""
        self.operation = ""
        self.op_mode = ""
        self.target_temp = ""
        self.room_temp = ""
        self.wind_strength = ""
        self.h_step = ""
        self.v_step = ""
        self.power = ""

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)

        if len(Devices) == 0:
            Domoticz.Device(Name="Operation", Unit=1, Image=16, TypeName="Switch", Used=1).Create()
            
            Options = {"LevelActions" : "|||||",
                       "LevelNames" : "|Auto|Cool|Heat|Fan|Dry",
                       "LevelOffHidden" : "true",
                       "SelectorStyle" : "0"}
                       
            Domoticz.Device(Name="Mode", Unit=2, TypeName="Selector Switch", Image=16, Options=Options, Used=1).Create()
            Domoticz.Device(Name="Setpoint", Unit=3, TypeName="Temperature", Used=1).Create()
            Domoticz.Device(Name="Room temp", Unit=4, TypeName="Temperature", Used=1).Create()
            
            Options = {"LevelActions" : "|||||||",
                       "LevelNames" : "|Auto|L2|L3|L4|L5|L6",
                       "LevelOffHidden" : "true",
                       "SelectorStyle" : "0"}
                       
            Domoticz.Device(Name="Fan speed", Unit=5, TypeName="Selector Switch", Image=7, Options=Options, Used=1).Create()
            
            
            Options = {"LevelActions" : "||||||||||",
                       "LevelNames" : "|Left-Right|None|Left|Mid-Left|Centre|Mid-Right|Right|Left-Centre|Centre-Right",
                       "LevelOffHidden" : "true",
                       "SelectorStyle" : "1"}
                       
            Domoticz.Device(Name="Swing Horizontal", Unit=6, TypeName="Selector Switch", Image=7, Options=Options, Used=1).Create()
            
            
            Options = {"LevelActions" : "|||||||||",
                       "LevelNames" : "|Top-Bottom|None|Top|1|2|3|4|Bottom",
                       "LevelOffHidden" : "true",
                       "SelectorStyle" : "1"}
                       
            Domoticz.Device(Name="Swing Vertical", Unit=7, TypeName="Selector Switch", Image=7, Options=Options, Used=1).Create()
            Domoticz.Device(Name="Power", Unit=8, TypeName="kWh", Used=1).Create()
            
            Domoticz.Log("LG ThinQ devices created.") 

        DumpConfigToLog()
        
        
        Protocol = "MQTT"
        if (Parameters["Port"] == "8883"): Protocol = "MQTTS"
        self.mqttConn = Domoticz.Connection(Name="MQTT Test", Transport="TCP/IP", Protocol=Protocol, Address=Parameters["Address"], Port=Parameters["Port"])
        self.mqttConn.Connect()

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Debug("MQTT connected successfully.")
            sendData = { 'Verb' : 'CONNECT',
                         'ID' : "645364363" }
            Connection.Send(sendData)

            Connection.Send({'Verb' : 'SUBSCRIBE', 'PacketIdentifier': 1001, 'Topics': [{'Topic':self.mqtt_topic, 'QoS': 0}]})        

        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

    def onMessage(self, Connection, Data):
        # Domoticz.Log("onMessage called with: "+Data["Verb"])
        # DumpDictionaryToLog(Data)
        
        if Data["Verb"] == "PUBLISH" and len(Data["Payload"]) > 0:
            # import web_pdb; web_pdb.set_trace()

            msg_parsed = json.loads(Data["Payload"].decode("utf-8"))
            status = msg_parsed["data"]["state"]["reported"]
            
            if Parameters["Mode6"] == "Debug":
                Domoticz.Log(status)
                
            # Check if there is our DeviceID in a message
            if msg_parsed["deviceId"] != Parameters["Mode2"]:
                return
            
            if Parameters["Mode1"] == "type_ac":
                
                # Operation
                if "airState.operation" in status:
                    self.operation = status["airState.operation"]
                    
                    if (self.operation == 0):
                        if (Devices[1].nValue != 0):
                            Devices[1].Update(nValue = 0, sValue ="0") 
                    else:
                        if (Devices[1].nValue != 1):
                            Devices[1].Update(nValue = 1, sValue ="100") 
                        
                    Domoticz.Log("operation received! Current: " + str(self.operation))
                    
                # Mode (opMode)
                if "airState.opMode" in status:
                    self.op_mode = str(status["airState.opMode"])
                    
                    if (self.op_mode == "6"):
                        sValueNew = "10" #Auto
                    elif (self.op_mode == "0"):
                        sValueNew = "20" #Cool
                    elif (self.op_mode == "4"):
                        sValueNew = "30" #Heat
                    elif (self.op_mode == "2"):
                        sValueNew = "40" #Fan
                    elif (self.op_mode == "1"):
                        sValueNew = "50" #Dry
                        
                    if(Devices[2].nValue != self.operation or Devices[2].sValue != sValueNew):
                        Devices[2].Update(nValue = self.operation, sValue = sValueNew)
                        Domoticz.Log("opMode received! Current: " + self.op_mode)
                    
                # Target temp (tempState.target)
                if "airState.tempState.target" in status:
                    self.target_temp = str(status["airState.tempState.target"])
                    
                    if (Devices[3].nValue != self.operation or Devices[3].sValue != self.target_temp):
                        Devices[3].Update(nValue = self.operation, sValue = self.target_temp)
                        Domoticz.Log("tempState.target received! Current: " + self.target_temp)
                        
                # Room temp (tempState.current)
                if "airState.tempState.current" in status:
                    room_temp = str(status["airState.tempState.current"])
                    
                    if (Devices[4].sValue != room_temp):
                        Devices[4].Update(nValue = 0, sValue = room_temp)
                        Domoticz.Log("tempState.current received! Current: " + room_temp)
                    else:
                        Domoticz.Log("Devices[4].sValue=" + Devices[4].sValue)
                        Domoticz.Log("room_temp=" + room_temp)
                    
                # Fan speed (windStrength)
                if "airState.windStrength" in status:
                    windStrength = str(status["airState.windStrength"])
                    
                    if (windStrength == "8"):
                        sValueNew = "10" #Auto
                    elif (windStrength == "2"):
                        sValueNew = "20" #2
                    elif (windStrength == "3"):
                        sValueNew = "30" #3
                    elif (windStrength == "4"):
                        sValueNew = "40" #4
                    elif (windStrength == "5"):
                        sValueNew = "50" #5
                    elif (windStrength == "6"):
                        sValueNew = "60" #6
                        
                    Devices[5].Update(nValue = 0, sValue = sValueNew)
                    Domoticz.Log("windStrength received! Current: " + windStrength)
                    
                # Swing Horizontal (hStep)
                if "airState.wDir.hStep" in status:
                    hStep = str(status["airState.wDir.hStep"])
                    
                    if (hStep == "100"):
                        sValueNew = "10" #Left-Right
                    elif (hStep == "1"):
                        sValueNew = "30" #Left
                    elif (hStep == "2"):
                        sValueNew = "40" #Middle-Left
                    elif (hStep == "3"):
                        sValueNew = "50" #Central
                    elif (hStep == "4"):
                        sValueNew = "60" #Middle-Right
                    elif (hStep == "5"):
                        sValueNew = "70" #Right
                    elif (hStep == "13"):
                        sValueNew = "80" #Left-Middle
                    elif (hStep == "35"):
                        sValueNew = "90" #Middle-Right
                    elif (hStep == "0"):
                        sValueNew = "70" #None
                        
                    Devices[6].Update(nValue = 0, sValue = sValueNew)
                    Domoticz.Log("hStep received! Current: " + hStep)
                    
                # Swing Vertival (vStep)
                if "airState.wDir.vStep" in status:
                    vStep = str(status["airState.wDir.vStep"])
                    
                    if (vStep == "100"):
                        sValueNew = "10" #Up-Down
                    elif (vStep == "0"):
                        sValueNew = "20" #None
                    elif (vStep == "1"):
                        sValueNew = "30" #Top
                    elif (vStep == "2"):
                        sValueNew = "40" #2
                    elif (vStep == "3"):
                        sValueNew = "50" #3
                    elif (vStep == "4"):
                        sValueNew = "60" #4
                    elif (vStep == "5"):
                        sValueNew = "70" #5
                    elif (vStep == "6"):
                        sValueNew = "80" #Bottom
                        
                    Devices[7].Update(nValue = 0, sValue = sValueNew)
                    Domoticz.Log("vStep received! Current: " + vStep)
                    
                # Current Power (energy.onCurrent)
                if "airState.energy.onCurrent" in status:
                    power = str(status["airState.energy.onCurrent"])
                    
                    Devices[8].Update(nValue = 0, sValue = power + ";0")
                    Domoticz.Log("power received! Current: " + power)
                
                
            # Domoticz.Log("data: " + msg_parsed["data"])
            # Domoticz.Log("state: " + msg_parsed["data"]["state"])
            # Domoticz.Log("reported: " + msg_parsed["data"]["state"]["reported"])

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        # Domoticz.Log("onHeartbeat called: "+str(self.counter))
        if (self.mqttConn.Connected()):
            if ((self.counter % 6) == 0):
                self.mqttConn.Send({ 'Verb' : 'PING' })
           
           # if (self.counter == 1):
               # self.mqttConn.Send({'Verb' : 'SUBSCRIBE', 'PacketIdentifier': 1001, 'Topics': [{'Topic':Parameters["Mode1"], 'QoS': 0}]})
           # elif ((self.counter % 6) == 0):
               # self.mqttConn.Send({ 'Verb' : 'PING' })
           # elif (self.counter == 10):
               # self.mqttConn.Send({'Verb' : 'UNSUBSCRIBE', 'Topics': [Parameters["Mode1"]]})
           # elif (self.counter == 50):
               # self.mqttConn.Send({ 'Verb' : 'DISCONNECT' })
            self.counter = self.counter + 1

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def DumpDictionaryToLog(theDict, Depth=""):
    if isinstance(theDict, dict):
        for x in theDict:
            if isinstance(theDict[x], dict):
                Domoticz.Log(Depth+"> Dict '"+x+"' ("+str(len(theDict[x]))+"):")
                DumpDictionaryToLog(theDict[x], Depth+"---")
            elif isinstance(theDict[x], list):
                Domoticz.Log(Depth+"> List '"+x+"' ("+str(len(theDict[x]))+"):")
                DumpListToLog(theDict[x], Depth+"---")
            elif isinstance(theDict[x], str):
                Domoticz.Log(Depth+">'" + x + "':'" + str(theDict[x]) + "'")
            else:
                Domoticz.Log(Depth+">'" + x + "': " + str(theDict[x]))

def DumpListToLog(theList, Depth):
    if isinstance(theList, list):
        for x in theList:
            if isinstance(x, dict):
                Domoticz.Log(Depth+"> Dict ("+str(len(x))+"):")
                DumpDictionaryToLog(x, Depth+"---")
            elif isinstance(x, list):
                Domoticz.Log(Depth+"> List ("+str(len(theList))+"):")
                DumpListToLog(x, Depth+"---")
            elif isinstance(x, str):
                Domoticz.Log(Depth+">'" + x + "':'" + str(theList[x]) + "'")
            else:
                Domoticz.Log(Depth+">'" + x + "': " + str(theList[x]))

