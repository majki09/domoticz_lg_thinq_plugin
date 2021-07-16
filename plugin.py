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
            <li>Control unit with LG API</li>
        </ul>
        <h3>Compatible devices</h3>
        <ul style="list-style-type:square">
            <li>AC - Air Conditioning (tested with LG PC12SQ unit).</li>
        </ul>
        <br/>
    </description>
    <params>
        <param field="Mode3" label="country" width="50px" />
        <param field="Mode4" label="language" width="50px" />
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
        <param field="Mode2" label="Device ID" width="270px"/>
    </params>
</plugin>
"""


        # <param field="Address" label="MQTT broker IP Address" width="100px" required="true" default="test.mosquitto.org"/>
        # <param field="Port" label="MQTT Connection" required="true" width="100px">
            # <options>
                # <option label="Unencrypted" value="1883" default="true" />
                # <option label="Encrypted" value="8883" />
                # <option label="Encrypted (Client Certificate)" value="8884" />
            # </options>
        # </param>
        # <param field="Username" label="MQTT broker Username" width="100px"/>
        # <param field="Password" label="MQTT broker Password" width="100px"/>
        
        
import Domoticz
import json
import random

import example
import wideq


# class LGDevice:
    # def __init__(self):


class BasePlugin:
    enabled = False
    # mqttConn = None
    counter = 0
    
    ac = None
    ac_status = None
    # mqtt_topic = "lg_thinq"
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
            Domoticz.Device(Name="Target temp", Unit=3, TypeName="Temperature", Used=1).Create()
            # devicecreated.append(deviceparam(3, 0, "24"))  # default is 24 degrees
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
        
        
        # self.ac = example.example("PL", "en-US", False, Parameters["Mode2"])
        [self.client, self.ac] = example.example(Parameters["Mode3"], Parameters["Mode4"], False, Parameters["Mode2"])
        self.ac.monitor_start()
        
        
        # Protocol = "MQTT"
        # if (Parameters["Port"] == "8883"): Protocol = "MQTTS"
        # self.mqttConn = Domoticz.Connection(Name="MQTT Test", Transport="TCP/IP", Protocol=Protocol, Address=Parameters["Address"], Port=Parameters["Port"])
        # self.mqttConn.Connect()

    def onStop(self):
        Domoticz.Log("onStop called")
        self.ac.monitor_stop()
        
    def onConnect(self, Connection, Status, Description):
        pass
        # if (Status == 0):
            # Domoticz.Debug("MQTT connected successfully.")
            # sendData = { 'Verb' : 'CONNECT',
                         # 'ID' : "645364363" }
            # Connection.Send(sendData)

            # Connection.Send({'Verb' : 'SUBSCRIBE', 'PacketIdentifier': 1001, 'Topics': [{'Topic':self.mqtt_topic, 'QoS': 0}]})        

        # else:
            # Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

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
                pass

                
                
            # Domoticz.Log("data: " + msg_parsed["data"])
            # Domoticz.Log("state: " + msg_parsed["data"]["state"])
            # Domoticz.Log("reported: " + msg_parsed["data"]["state"]["reported"])
            
    def onCommand(self, Unit, Command, Level, Hue):
        # Domoticz.Debug("Command received U="+str(Unit)+" C="+str(Command)+" L= "+str(Level)+" H= "+str(Hue))
        # import web_pdb; web_pdb.set_trace()
        
        if (Unit == 1):
            if(Command == "On"):
                self.operation = 1
                self.ac.set_on(True)
            else:
                self.operation = 0
                self.ac.set_on(False)
                
        if (Unit == 2): # opMode
            if (Level == 10):
                self.ac.set_mode(wideq.ACMode.ACO)
            elif (Level == 20):
                self.ac.set_mode(wideq.ACMode.COOL)
            elif (Level == 30):
                self.ac.set_mode(wideq.ACMode.HEAT)
            elif (Level == 40):
                self.ac.set_mode(wideq.ACMode.FAN)
            elif (Level == 50):
                self.ac.set_mode(wideq.ACMode.DRY)
                
        if (Unit == 5): # Fan speed
            if (Level == 10):
                self.ac.set_fan_speed(wideq.ACFanSpeed.NATURE)
            elif (Level == 20):
                self.ac.set_fan_speed(wideq.ACFanSpeed.LOW)
            elif (Level == 30):
                self.ac.set_fan_speed(wideq.ACFanSpeed.LOW_MID)
            elif (Level == 40):
                self.ac.set_fan_speed(wideq.ACFanSpeed.MID)
            elif (Level == 50):
                self.ac.set_fan_speed(wideq.ACFanSpeed.MID_HIGH)
            elif (Level == 60):
                self.ac.set_fan_speed(wideq.ACFanSpeed.HIGH)
                
        if (Unit == 6): # Swing horizontal
            if (Level == 10):
                self.ac.set_horz_swing(wideq.ACHSwingMode.ALL)
            elif (Level == 20):
                self.ac.set_horz_swing(wideq.ACHSwingMode.OFF)
            elif (Level == 30):
                self.ac.set_horz_swing(wideq.ACHSwingMode.ONE)
            elif (Level == 40):
                self.ac.set_horz_swing(wideq.ACHSwingMode.TWO)
            elif (Level == 50):
                self.ac.set_horz_swing(wideq.ACHSwingMode.THREE)
            elif (Level == 60):
                self.ac.set_horz_swing(wideq.ACHSwingMode.FOUR)
            elif (Level == 70):
                self.ac.set_horz_swing(wideq.ACHSwingMode.FIVE)
            elif (Level == 80):
                self.ac.set_horz_swing(wideq.ACHSwingMode.LEFT_HALF)
            elif (Level == 90):
                self.ac.set_horz_swing(wideq.ACHSwingMode.RIGHT_HALF)
                
        if (Unit == 7): # Swing vertical
            if (Level == 10):
                self.ac.set_vert_swing(wideq.ACVSwingMode.ALL)
            elif (Level == 20):
                self.ac.set_vert_swing(wideq.ACVSwingMode.OFF)
            elif (Level == 30):
                self.ac.set_vert_swing(wideq.ACVSwingMode.ONE)
            elif (Level == 40):
                self.ac.set_vert_swing(wideq.ACVSwingMode.TWO)
            elif (Level == 50):
                self.ac.set_vert_swing(wideq.ACVSwingMode.THREE)
            elif (Level == 60):
                self.ac.set_vert_swing(wideq.ACVSwingMode.FOUR)
            elif (Level == 70):
                self.ac.set_vert_swing(wideq.ACVSwingMode.FIVE)
            elif (Level == 80):
                self.ac.set_vert_swing(wideq.ACVSwingMode.SIX)
            
            # Update state of all other devices
            # Devices[4].Update(nValue = self.operation, sValue = Devices[4].sValue)
            # Devices[5].Update(nValue = self.operation, sValue = Devices[5].sValue)
            # Devices[6].Update(nValue = self.operation, sValue = Devices[6].sValue)
        
        # if (Unit == 4):
            # Devices[4].Update(nValue = self.operation, sValue = str(Level))
            
        # if (Unit == 5):
            # Devices[5].Update(nValue = self.operation, sValue = str(Level))
        
        # if (Unit == 6):
            # Devices[6].Update(nValue = self.operation, sValue = str(Level))
            
        # self.httpConnSetControl.Connect()
        
    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")
        self.ac.monitor_stop()

    def onHeartbeat(self):
        # Domoticz.Log("onHeartbeat called: "+str(self.counter))
        # import web_pdb; web_pdb.set_trace()
        
        try:
            self.ac_status = self.ac.poll()
        
            self.operation = self.ac_status.is_on
            if self.operation == True:
                self.operation = 1
            else:
                self.operation = 0
                
            self.op_mode = self.ac_status.mode.name
            self.target_temp = str(self.ac_status.temp_cfg_c)
            self.room_temp = str(self.ac_status.temp_cur_c)
            self.wind_strength = self.ac_status.fan_speed.name
            self.h_step = self.ac_status.horz_swing.name
            self.v_step = self.ac_status.vert_swing.name
            self.power = str(self.ac_status.energy_on_current)
            
            # if (self.mqttConn.Connected()):
                # if ((self.counter % 6) == 0):
                    # self.mqttConn.Send({ 'Verb' : 'PING' })
               
               # if (self.counter == 1):
                   # self.mqttConn.Send({'Verb' : 'SUBSCRIBE', 'PacketIdentifier': 1001, 'Topics': [{'Topic':Parameters["Mode1"], 'QoS': 0}]})
               # elif ((self.counter % 6) == 0):
                   # self.mqttConn.Send({ 'Verb' : 'PING' })
               # elif (self.counter == 10):
                   # self.mqttConn.Send({'Verb' : 'UNSUBSCRIBE', 'Topics': [Parameters["Mode1"]]})
               # elif (self.counter == 50):
                   # self.mqttConn.Send({ 'Verb' : 'DISCONNECT' })
            self.counter = self.counter + 1
            
            self.update_domoticz()
        except wideq.NotLoggedInError:
            Domoticz.Log("Session expired, refreshing...")
            self.client.refresh()
        
    def update_domoticz(self):
        # import web_pdb; web_pdb.set_trace()
        # Operation
        if (self.operation == 0):
            if (Devices[1].nValue != 0):
                Devices[1].Update(nValue = 0, sValue ="0") 
                Domoticz.Log("operation received! Current: " + str(self.operation))
        else:
            if (Devices[1].nValue != 1):
                Devices[1].Update(nValue = 1, sValue ="100")
                Domoticz.Log("operation received! Current: " + str(self.operation))
            
        # Mode (opMode)
        if (self.op_mode == "ACO"):
            sValueNew = "10" #Auto
        elif (self.op_mode == "COOL"):
            sValueNew = "20" #Cool
        elif (self.op_mode == "HEAT"):
            sValueNew = "30" #Heat
        elif (self.op_mode == "FAN"):
            sValueNew = "40" #Fan
        elif (self.op_mode == "DRY"):
            sValueNew = "50" #Dry
            
        if(Devices[2].nValue != self.operation or Devices[2].sValue != sValueNew):
            Devices[2].Update(nValue = self.operation, sValue = sValueNew)
            Domoticz.Log("Mode received! Current: " + self.op_mode)
            
        # Target temp (tempState.target)
        if (Devices[3].nValue != self.operation or Devices[3].sValue != self.target_temp):
            Devices[3].Update(nValue = self.operation, sValue = self.target_temp)
            Domoticz.Log("tempState.target received! Current: " + self.target_temp)
                
        # Room temp (tempState.current)
        if (Devices[4].sValue != self.room_temp):
            Devices[4].Update(nValue = 0, sValue = self.room_temp)
            Domoticz.Log("tempState.current received! Current: " + self.room_temp)
        # else:
            # Domoticz.Log("Devices[4].sValue=" + Devices[4].sValue)
            # Domoticz.Log("room_temp=" + self.room_temp)
            
        # Fan speed (windStrength)
        if (self.wind_strength == "NATURE"):
            sValueNew = "10" #Auto
        elif (self.wind_strength == "LOW"):
            sValueNew = "20" #2
        elif (self.wind_strength == "LOW_MID"):
            sValueNew = "30" #3
        elif (self.wind_strength == "MID"):
            sValueNew = "40" #4
        elif (self.wind_strength == "MID_HIGH"):
            sValueNew = "50" #5
        elif (self.wind_strength == "HIGH"):
            sValueNew = "60" #6
                
        if (Devices[5].nValue != self.operation or Devices[5].sValue != sValueNew):
            # Domoticz.Log(str(Devices[5].nValue))
            # Domoticz.Log("operation=" + str(self.operation))
            # Domoticz.Log(Devices[5].sValue)
            # Domoticz.Log(sValueNew)
            Devices[5].Update(nValue = self.operation, sValue = sValueNew)
            Domoticz.Log("windStrength received! Current: " + self.wind_strength)
            
        # Swing Horizontal (hStep)
        if (self.h_step == "ALL"):
            sValueNew = "10" #Left-Right
        elif (self.h_step == "ONE"):
            sValueNew = "30" #Left
        elif (self.h_step == "TWO"):
            sValueNew = "40" #Middle-Left
        elif (self.h_step == "THREE"):
            sValueNew = "50" #Central
        elif (self.h_step == "FOUR"):
            sValueNew = "60" #Middle-Right
        elif (self.h_step == "FIVE"):
            sValueNew = "70" #Right
        elif (self.h_step == "LEFT_HALF"):
            sValueNew = "80" #Left-Middle
        elif (self.h_step == "RIGHT_HALF"):
            sValueNew = "90" #Middle-Right
        elif (self.h_step == "OFF"):
            sValueNew = "20" #None
            
        if (Devices[6].nValue != self.operation or Devices[6].sValue != sValueNew):
            Devices[6].Update(nValue = self.operation, sValue = sValueNew)
            Domoticz.Log("hStep received! Current: " + self.h_step)
            
        # Swing Vertival (vStep)
        if (self.v_step == "ALL"):
            sValueNew = "10" #Up-Down
        elif (self.v_step == "OFF"):
            sValueNew = "20" #None
        elif (self.v_step == "ONE"):
            sValueNew = "30" #Top
        elif (self.v_step == "TWO"):
            sValueNew = "40" #2
        elif (self.v_step == "THREE"):
            sValueNew = "50" #3
        elif (self.v_step == "FOUR"):
            sValueNew = "60" #4
        elif (self.v_step == "FIVE"):
            sValueNew = "70" #5
        elif (self.v_step == "SIX"):
            sValueNew = "80" #Bottom
            
        if (Devices[7].nValue != self.operation or Devices[7].sValue != sValueNew):   
            Devices[7].Update(nValue = self.operation, sValue = sValueNew)
            Domoticz.Log("vStep received! Current: " + self.v_step)
  #          
  #      # Current Power (energy.onCurrent)
  #      if "airState.energy.onCurrent" in status:
  #          power = str(status["airState.energy.onCurrent"])
  #          
  #          Devices[8].Update(nValue = 0, sValue = power + ";0")
  #          Domoticz.Log("power received! Current: " + power)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

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

