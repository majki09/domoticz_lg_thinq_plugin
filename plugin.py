#!/usr/bin/python3

# Python Plugin LG ThinQ API v2 integration.
#
# Author: majki
#
"""
<plugin key="LG_ThinQ" name="LG ThinQ" author="majki" version="2.1.1" externallink="https://github.com/majki09/domoticz_lg_thinq_plugin">
    <description>
        <h2>LG ThinQ domoticz plugin</h2><br/>
        Plugin uses LG API v2. All API interface (with some mods) comes from <a href="https://github.com/no2chem/wideq"> github.com/no2chem/wideq</a>.<br/><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Reading unit parameters from LG ThinQ API</li>
            <li>Control unit with LG ThinQ API</li>
        </ul>
        <h3>Tested and working devices</h3>
        <h4>Air Conditioners (AC)</h4>
        <ul style="list-style-type:square">
            <li>LG AP12RT NSJ</li>
            <li>LG PC12SQ</li>
        </ul>
        <h4>Air-to-Water Heat Pumps (AWHP)</h4>
        <ul style="list-style-type:square">
            <li>LG therma V 7kW HN0916M NK4</li>
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
        <param field="Mode1" label="Device type" width="270px">
            <options>
                <option label="Air Conditioning (AC)" value="type_ac" default="true" />
                <option label="Air to Water Heat Pump (AWHP)" value="type_awhp" default="false" />
            </options>
        </param>
        <param field="Mode2" label="Device ID" width="270px"/>
    </params>
</plugin>
"""

import Domoticz
import json
import os.path

import wideq


class BasePlugin:
    enabled = False
    heartbeat_counter = 0
    
    ac_status = None
    
    def __init__(self):
        # values will be filled in with onStart function
        self.DEVICE_TYPE = ""
        self.DEVICE_ID = ""
        self.COUNTRY = ""
        self.LANGUAGE = ""
        self.DEBUG = ""

        self.device_id = ""
        self.operation = ""
        self.op_mode = ""
        self.target_temp = ""
        self.hot_water_temp = ""
        self.room_temp = ""
        self.in_water_temp = ""
        self.out_water_temp = ""
        self.wind_strength = ""
        self.h_step = ""
        self.v_step = ""
        # self.power = ""

        self.lg_device = None
        self.state = {}

    def onStart(self):
        # these variables definitions has to be here (onStart)
        self.DEVICE_TYPE = Parameters["Mode1"]
        self.DEVICE_ID = Parameters["Mode2"]
        self.COUNTRY = Parameters["Mode3"]
        self.LANGUAGE = Parameters["Mode4"]
        self.DEBUG = Parameters["Mode6"]

        if self.DEBUG == "Debug":
            Domoticz.Debugging(1)

        self.wideq_object = WideQ(country=self.COUNTRY,
                                  language=self.LANGUAGE)

        if self.wideq_object.state_file == "":
            return False

        # import web_pdb; web_pdb.set_trace()

        try:
            # read AC parameters and Client state
            self.lg_device = self.wideq_object.operate_device(device_id=self.DEVICE_ID)

        except UserWarning:
            Domoticz.Error("Device not found on your LG account. Check your device ID.")

        if self.lg_device is None:
            return False

        # AC part
        if self.DEVICE_TYPE == "type_ac":
            Domoticz.Log("Getting AC status successful.")
            if len(Devices) == 0:
                Domoticz.Device(Name="Operation", Unit=1, Image=16, TypeName="Switch", Used=1).Create()
                
                Options = {"LevelActions" : "|||||",
                           "LevelNames" : "|Auto|Cool|Heat|Fan|Dry",
                           "LevelOffHidden" : "true",
                           "SelectorStyle" : "0"}
                           
                Domoticz.Device(Name="Mode", Unit=2, TypeName="Selector Switch", Image=16, Options=Options, Used=1).Create()
                Domoticz.Device(Name="Target temp", Unit=3, Type=242, Subtype=1, Image=15, Used=1).Create()
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
                # Domoticz.Device(Name="Power", Unit=8, TypeName="kWh", Used=1).Create()
                
                Domoticz.Log("LG ThinQ AC device created.")
                
        # AWHP part
        elif self.DEVICE_TYPE == "type_awhp":
            Domoticz.Log("Getting AWHP status successful.")
            if len(Devices) == 0:
                Domoticz.Device(Name="Operation", Unit=1, Image=16, TypeName="Switch", Used=1).Create()
                
                Options = {"LevelActions" : "||||",
                           "LevelNames" : "|Cool|AI|Heat",
                           "LevelOffHidden" : "true",
                           "SelectorStyle" : "0"}
                           
                Domoticz.Device(Name="Mode", Unit=2, TypeName="Selector Switch", Image=16, Options=Options, Used=1).Create()
                Domoticz.Device(Name="Target temp", Unit=3, Type=242, Subtype=1, Image=15, Used=1).Create()
                Domoticz.Device(Name="Hot water temp", Unit=4, Type=242, Subtype=1, Image=15, Used=1).Create()
                Domoticz.Device(Name="Input water temp", Unit=5, TypeName="Temperature", Used=1).Create()
                Domoticz.Device(Name="Output water temp", Unit=6, TypeName="Temperature", Used=1).Create()
                
                Domoticz.Log("LG ThinQ AWHP device created.") 
        else:
            Domoticz.Error("Getting LG device status failed.")

        DumpConfigToLog()

    def onStop(self):
        Domoticz.Log("onStop called")
        
    def onConnect(self, Connection, Status, Description):
        pass

    def onMessage(self, Connection, Data):
        # Domoticz.Log("onMessage called with: "+Data["Verb"])
        # DumpDictionaryToLog(Data)
        
        pass
            
    def onCommand(self, Unit, Command, Level, Hue):
        # Domoticz.Debug("Command received U="+str(Unit)+" C="+str(Command)+" L= "+str(Level)+" H= "+str(Hue))
        # import web_pdb; web_pdb.set_trace()
        
        # AC part
        if self.DEVICE_TYPE == "type_ac":
            if Unit == 1: # Operation
                if Command == "On":
                    self.operation = 1
                    self.lg_device.set_on(True)
                    Devices[1].Update(nValue = 1, sValue = "100") 
                else:
                    self.operation = 0
                    self.lg_device.set_on(False)
                    Devices[1].Update(nValue = 0, sValue = "0") 
                    
            if Unit == 2: # opMode
                newImage = 16
                if Level == 10:
                    self.lg_device.set_mode(wideq.ACMode.ACO)
                    newImage = 16
                elif Level == 20:
                    self.lg_device.set_mode(wideq.ACMode.COOL)
                    newImage = 16
                elif Level == 30:
                    self.lg_device.set_mode(wideq.ACMode.HEAT)
                    newImage = 15
                elif Level == 40:
                    self.lg_device.set_mode(wideq.ACMode.FAN)
                    newImage = 7
                elif Level == 50:
                    self.lg_device.set_mode(wideq.ACMode.DRY)
                    newImage = 16
                Devices[2].Update(nValue = self.operation, sValue = str(Level), Image = newImage)
                    
            if Unit == 3: # SetPoint
                # import web_pdb; web_pdb.set_trace()
                if Devices[3].nValue != self.operation or Devices[3].sValue != Level:
                    self.lg_device.set_celsius(int(Level))
                    Domoticz.Log("new Setpoint: " + str(Level))
                    Devices[3].Update(nValue = self.operation, sValue = str(Level))
                    
            if Unit == 5: # Fan speed
                # import web_pdb; web_pdb.set_trace()
                if Level == 10:
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.NATURE)
                elif Level == 20:
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.LOW)
                elif Level == 30:
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.LOW_MID)
                elif Level == 40:
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.MID)
                elif Level == 50:
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.MID_HIGH)
                elif Level == 60:
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.HIGH)
                Devices[5].Update(nValue = self.operation, sValue = str(Level))
                    
            if Unit == 6: # Swing horizontal
                if Level == 10:
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.ALL)
                elif Level == 20:
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.OFF)
                elif Level == 30:
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.ONE)
                elif Level == 40:
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.TWO)
                elif Level == 50:
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.THREE)
                elif Level == 60:
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.FOUR)
                elif Level == 70:
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.FIVE)
                elif Level == 80:
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.LEFT_HALF)
                elif Level == 90:
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.RIGHT_HALF)
                Devices[6].Update(nValue = self.operation, sValue = str(Level))
                    
            if Unit == 7: # Swing vertical
                if Level == 10:
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.ALL)
                elif Level == 20:
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.OFF)
                elif Level == 30:
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.ONE)
                elif Level == 40:
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.TWO)
                elif Level == 50:
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.THREE)
                elif Level == 60:
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.FOUR)
                elif Level == 70:
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.FIVE)
                elif Level == 80:
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.SIX)
                Devices[7].Update(nValue = self.operation, sValue = str(Level))
                
            
        # AWHP part
        if self.DEVICE_TYPE == "type_awhp":
            if Unit == 1: # Operation
                if Command == "On":
                    self.operation = 1
                    self.lg_device.set_on(True)
                    Devices[1].Update(nValue = 1, sValue = "100") 
                else:
                    self.operation = 0
                    self.lg_device.set_on(False)
                    Devices[1].Update(nValue = 0, sValue = "0") 
                    
            if Unit == 2: # opMode
                newImage = 16
                if Level == 10:
                    self.lg_device.set_mode(wideq.ACMode.COOL)
                    newImage = 16
                elif Level == 20:
                    self.lg_device.set_mode(wideq.ACMode.AI)
                    newImage = 16
                elif Level == 30:
                    self.lg_device.set_mode(wideq.ACMode.HEAT)
                    newImage = 15
                Devices[2].Update(nValue = self.operation, sValue = str(Level), Image = newImage)
                    
            if Unit == 3: # Target temp
                if Devices[3].nValue != self.operation or Devices[3].sValue != Level:
                    self.lg_device.set_celsius(int(Level))
                    Domoticz.Log("new Target temp: " + str(Level))
                    Devices[3].Update(nValue = self.operation, sValue = str(Level))
                    
            if Unit == 4: # Hot water temp
                if Devices[4].nValue != self.operation or Devices[4].sValue != Level:
                    self.lg_device.set_hot_water(int(Level))
                    Domoticz.Log("new Hot water Target temp: " + str(Level))
                    Devices[4].Update(nValue = self.operation, sValue = str(Level))
        
    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    # every 5 seconds
    def onHeartbeat(self):
        # Domoticz.Log("onHeartbeat called: "+str(self.heartbeat_counter))
        if (self.heartbeat_counter % 6) == 0:
            # Domoticz.Log("onHeartbeat %6 called: "+str(self.heartbeat_counter))
            # import web_pdb; web_pdb.set_trace()
            # to check if self.lg_device has been already read out from server
            if self.lg_device is not None:
        
                try:
                    self.lg_device_status = self.lg_device.get_status()
                    
                    # AC part
                    if self.DEVICE_TYPE == "type_ac":
                        self.operation = self.lg_device_status.is_on
                        if self.operation:
                            self.operation = 1
                        else:
                            self.operation = 0
                            
                        self.op_mode = self.lg_device_status.mode.name
                        self.target_temp = str(self.lg_device_status.temp_cfg_c)
                        self.room_temp = str(self.lg_device_status.temp_cur_c)
                        self.wind_strength = self.lg_device_status.fan_speed.name
                        self.h_step = self.lg_device_status.horz_swing.name
                        self.v_step = self.lg_device_status.vert_swing.name
                        # self.power = str(self.lg_device_status.energy_on_current)
                        
                    # AWHP part
                    if self.DEVICE_TYPE == "type_awhp":
                        self.operation = self.lg_device_status.is_on
                        if self.operation:
                            self.operation = 1
                        else:
                            self.operation = 0
                            
                        self.op_mode = self.lg_device_status.mode.name
                        self.target_temp = str(self.lg_device_status.temp_cfg_c)
                        self.hot_water_temp = str(self.lg_device_status.temp_hot_water_cfg_c)
                        self.in_water_temp = str(self.lg_device_status.in_water_cur_c)
                        self.out_water_temp = str(self.lg_device_status.out_water_cur_c)
                        
                    self.update_domoticz()
                        
                except wideq.NotLoggedInError:
            
                    # read AC parameters and Client state
                    Domoticz.Log("Session expired, refreshing...")
                    self.lg_device = self.wideq_object.operate_device(device_id=self.DEVICE_ID)
                            
        self.heartbeat_counter = self.heartbeat_counter + 1
        if self.heartbeat_counter > 6:
            self.heartbeat_counter = 0
        
    def update_domoticz(self):
        # import web_pdb; web_pdb.set_trace()
        # AC part
        if self.DEVICE_TYPE == "type_ac":
            # Operation
            if self.operation == 0:
                if Devices[1].nValue != 0:
                    Devices[1].Update(nValue = 0, sValue ="0") 
                    Domoticz.Log("operation received! Current: " + str(self.operation))
            else:
                if Devices[1].nValue != 1:
                    Devices[1].Update(nValue = 1, sValue ="100")
                    Domoticz.Log("operation received! Current: " + str(self.operation))
                
            # Mode (opMode)
            if self.op_mode == "ACO":
                sValueNew = "10" #Auto
                newImage = 16
            elif self.op_mode == "COOL":
                sValueNew = "20" #Cool
                newImage = 16
            elif self.op_mode == "HEAT":
                sValueNew = "30" #Heat
                newImage = 15
            elif self.op_mode == "FAN":
                sValueNew = "40" #Fan
                newImage = 7
            elif self.op_mode == "DRY":
                sValueNew = "50" #Dry
                newImage = 16
                
            if Devices[2].nValue != self.operation or Devices[2].sValue != sValueNew:
                Devices[2].Update(nValue = self.operation, sValue = sValueNew, Image = newImage)
                Domoticz.Log("Mode received! Current: " + self.op_mode)
                
            # Target temp (tempState.target)
            if Devices[3].nValue != self.operation or Devices[3].sValue != self.target_temp:
                Devices[3].Update(nValue = self.operation, sValue = self.target_temp)
                Domoticz.Log("tempState.target received! Current: " + self.target_temp)
                    
            # Room temp (tempState.current)
            if Devices[4].sValue != self.room_temp:
                Devices[4].Update(nValue = 0, sValue = self.room_temp)
                Domoticz.Log("tempState.current received! Current: " + self.room_temp)
            # else:
                # Domoticz.Log("Devices[4].sValue=" + Devices[4].sValue)
                # Domoticz.Log("room_temp=" + self.room_temp)
                
            # Fan speed (windStrength)
            if self.wind_strength == "NATURE":
                sValueNew = "10" #Auto
            elif self.wind_strength == "LOW":
                sValueNew = "20" #2
            elif self.wind_strength == "LOW_MID":
                sValueNew = "30" #3
            elif self.wind_strength == "MID":
                sValueNew = "40" #4
            elif self.wind_strength == "MID_HIGH":
                sValueNew = "50" #5
            elif self.wind_strength == "HIGH":
                sValueNew = "60" #6
                    
            if Devices[5].nValue != self.operation or Devices[5].sValue != sValueNew:
                Devices[5].Update(nValue = self.operation, sValue = sValueNew)
                Domoticz.Log("windStrength received! Current: " + self.wind_strength)
                
            # Swing Horizontal (hStep)
            if self.h_step == "ALL":
                sValueNew = "10" #Left-Right
            elif self.h_step == "ONE":
                sValueNew = "30" #Left
            elif self.h_step == "TWO":
                sValueNew = "40" #Middle-Left
            elif self.h_step == "THREE":
                sValueNew = "50" #Central
            elif self.h_step == "FOUR":
                sValueNew = "60" #Middle-Right
            elif self.h_step == "FIVE":
                sValueNew = "70" #Right
            elif self.h_step == "LEFT_HALF":
                sValueNew = "80" #Left-Middle
            elif self.h_step == "RIGHT_HALF":
                sValueNew = "90" #Middle-Right
            elif self.h_step == "OFF":
                sValueNew = "20" #None
                
            if Devices[6].nValue != self.operation or Devices[6].sValue != sValueNew:
                Devices[6].Update(nValue = self.operation, sValue = sValueNew)
                Domoticz.Log("hStep received! Current: " + self.h_step)
                
            # Swing Vertival (vStep)
            if self.v_step == "ALL":
                sValueNew = "10" #Up-Down
            elif self.v_step == "OFF":
                sValueNew = "20" #None
            elif self.v_step == "ONE":
                sValueNew = "30" #Top
            elif self.v_step == "TWO":
                sValueNew = "40" #2
            elif self.v_step == "THREE":
                sValueNew = "50" #3
            elif self.v_step == "FOUR":
                sValueNew = "60" #4
            elif self.v_step == "FIVE":
                sValueNew = "70" #5
            elif self.v_step == "SIX":
                sValueNew = "80" #Bottom
                
            if Devices[7].nValue != self.operation or Devices[7].sValue != sValueNew:
                Devices[7].Update(nValue = self.operation, sValue = sValueNew)
                Domoticz.Log("vStep received! Current: " + self.v_step)
                
            # Current Power (energy.onCurrent)
            # if (Devices[8].sValue != (str(self.power) + ";0")):
                # import web_pdb; web_pdb.set_trace()
                # Devices[8].Update(nValue = self.operation, sValue = self.power + ";0")
                # Domoticz.Log("power received! Current: " + self.power)

        # AWHP part
        if self.DEVICE_TYPE == "type_awhp":
            # Operation
            if self.operation == 0:
                if Devices[1].nValue != 0:
                    Devices[1].Update(nValue = 0, sValue ="0") 
                    Domoticz.Log("operation received! Current: " + str(self.operation))
            else:
                if Devices[1].nValue != 1:
                    Devices[1].Update(nValue = 1, sValue ="100")
                    Domoticz.Log("operation received! Current: " + str(self.operation))
                
            # Mode (opMode)
            if self.op_mode == "COOL":
                sValueNew = "10" #Auto
                newImage = 16
            elif self.op_mode == "AI":
                sValueNew = "20" #Cool
                newImage = 16
            elif self.op_mode == "HEAT":
                sValueNew = "30" #Heat
                newImage = 15
                
            if Devices[2].nValue != self.operation or Devices[2].sValue != sValueNew:
                Devices[2].Update(nValue = self.operation, sValue = sValueNew, Image = newImage)
                Domoticz.Log("Mode received! Current: " + self.op_mode)
                
            # Target temp (tempState.target)
            if Devices[3].nValue != self.operation or Devices[3].sValue != self.target_temp:
                Devices[3].Update(nValue = self.operation, sValue = self.target_temp)
                Domoticz.Log("tempState.target received! Current: " + self.target_temp)
                
            # Hot water temp (airState.tempState.hotWaterCurrent)
            if Devices[4].nValue != self.operation or Devices[4].sValue != self.hot_water_temp:
                Devices[4].Update(nValue = self.operation, sValue = self.hot_water_temp)
                Domoticz.Log("airState.tempState.hotWaterCurrent received! Current: " + self.hot_water_temp)
                
            # Input water temp (tempState.inWaterCurrent)
            if Devices[5].nValue != self.operation or Devices[5].sValue != self.in_water_temp:
                Devices[5].Update(nValue = self.operation, sValue = self.in_water_temp)
                Domoticz.Log("tempState.inWaterCurrent received! Current: " + self.in_water_temp)
                
            # Output water temp (tempState.outWaterCurrent)
            if Devices[6].nValue != self.operation or Devices[6].sValue != self.out_water_temp:
                Devices[6].Update(nValue = self.operation, sValue = self.out_water_temp)
                Domoticz.Log("tempState.outWaterCurrent received! Current: " + self.out_water_temp)

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


class UserError(Exception):
    """A user-visible command-line error."""

    def __init__(self, msg):
        self.msg = msg


class CompatibilityError(Exception):
    """A user-visible command-line error. Useful for raising non-V2 API exceptions."""

    def __init__(self, msg):
        self.msg = msg


class WideQ:
    STATE_FILE_NAME = "wideq_state.json"
    state_file: str = ""
    state: dict = {}

    country: str
    language: str

    def __init__(self, country, language):
        self.country = country
        self.language = language

        self.state_file = self.get_statefile_location()
        if self.state_file != "":
            self.state = self.load_state_from_file(self.state_file)

    def get_statefile_location(self) -> str:
        state_file = ""

        # determine the wideq_state file location
        # non-docker location
        try:
            loc_to_try = ".//plugins//domoticz_lg_thinq_plugin//" + self.STATE_FILE_NAME
            with open(loc_to_try, 'r'):
                state_file = loc_to_try
                Domoticz.Log("wideq_state file found in non-docker location.")
        except IOError:
            # Synology NAS location
            try:
                loc_to_try = ".//var//plugins//domoticz_lg_thinq_plugin//" + self.STATE_FILE_NAME
                with open(loc_to_try, 'r'):
                    state_file = loc_to_try
                    Domoticz.Log("wideq_state file found in Synology NAS location.")
            except IOError:
                # docker location
                try:
                    loc_to_try = ".//userdata//plugins//domoticz_lg_thinq_plugin//" + self.STATE_FILE_NAME
                    with open(loc_to_try, 'r'):
                        state_file = loc_to_try
                        Domoticz.Log("wideq_state file found in docker location.")
                except IOError:
                    try:
                        loc_to_try = self.STATE_FILE_NAME
                        with open(loc_to_try, 'r'):
                            state_file = loc_to_try
                            Domoticz.Log("wideq_state file found in default location.")
                    except IOError:
                        Domoticz.Error(f"wideq_state file not found!")

        return state_file

    def load_state_from_file(self, state_file: str) -> dict:
        state = {}

        try:
            with open(state_file) as f:
                Domoticz.Log(f"State data loaded from '{os.path.abspath(state_file)}'")
                state = json.load(f)
        except IOError:
            Domoticz.Error(f"No state file found (tried: '{os.path.abspath(state_file)}')")
        except json.decoder.JSONDecodeError:
            Domoticz.Error("Broken wideq_state.json file?")

        return state

    def authenticate(self, gateway):
        """Interactively authenticate the user via a browser to get an OAuth
        session.
        """

        login_url = gateway.oauth_url()
        print("Log in here:")
        print(login_url)
        print("Then paste the URL where the browser is redirected:")
        callback_url = input()
        return wideq.Auth.from_url(gateway, callback_url)

    def info(self, client, device_id):
        """Dump info on a device."""

        device = client.get_device(device_id)
        # pprint(vars(device), indent=4, width=1)
        return device.data

    def _force_device(self, client, device_id):
        """Look up a device in the client (using `get_device`), but raise
        UserError if the device is not found.
        """
        device = client.get_device(device_id)
        if not device:
            raise UserError(f'device "{device_id}" not found')
        if device.platform_type != "thinq2":
            raise CompatibilityError(f'Sorry, device "{device_id}" is V1 LG API and will NOT work with this domoticz plugin.')
        return device

    def operate_device(self, device_id: str = ""):
        lg_device = None

        client = wideq.Client.load(self.state)
        client._country = self.country
        client._language = self.language

        # Log in, if we don't already have an authentication.
        if not client._auth:
            client._auth = self.authenticate(client.gateway)

        # Loop to retry if session has expired.
        while True:
            try:
                if len(device_id) > 0:
                    lg_device = wideq.ACDevice(client, self._force_device(client, device_id))
                break

            except TypeError:
                Domoticz.Log("Could NOT log in. Probably you need to accept new agreement in the mobile app.")

            except wideq.NotLoggedInError or wideq.core.NotLoggedInError:
                Domoticz.Log("Session expired.")
                client.refresh()

            except UserError as exc:
                Domoticz.Error(exc.msg)
                raise UserWarning

            except CompatibilityError as exc:
                Domoticz.Error(exc.args[0])
                Domoticz.Error("You don't have any compatible (LG API V2) devices.")
                return None

        current_state = client.dump()
        # Save the updated state.
        if self.state != current_state:
            self.state = current_state
            with open(self.state_file, "w") as f:
                json.dump(current_state, f)
                Domoticz.Log(f"State written to state file '{os.path.abspath(self.state_file)}'")

        return lg_device
