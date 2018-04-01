#
# Logs traffic on the Dynamic Device Discovery port
#
# Works on Linux, Windows appears to filter out UDP from the network even when the firewall is set to allow it
#
# Useful IP Address and Port combinations that can be set via the Hardware page:
#    239.255.250.250:9161 - Dynamic Device Discovery (DDD) (default, shows Global Cache, Denon Amps and more)
#    239.255.255.250:1900 - Simple Service Discovery Protocol (SSDP), (shows Windows, Kodi, Denon, Chromebooks, Gateways, ...)
# Author: Dnpwwo, 2017
#
"""
<plugin key="UdpDiscover" name="UDP Discovery Example" author="dnpwwo" version="2.2.0">
    <params>
        <param field="Mode1" label="Discovery Type" width="275px">
            <options>
                <option label="Dynamic Device Discovery" value="239.255.250.250:9161"/>
                <option label="Simple Service Discovery Protocol" value="239.255.255.250:1900" />
                <option label="MySensors clone over UDP" value="255.255.255.255:9009"  default="true" />
            </options>
        </param>
        <param field="Mode2" label="Create Devices" width="75px">
            <options>
                <option label="True" value="True"/>
                <option label="False" value="False"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import mySensorsConst as const
from mySensorsMessage import MySensorsMessage

class BasePlugin:
    BeaconConn = None

    def __init__(self):
        return

    def onStart(self):
        # Test by creating few different devices
        #Domoticz.Device("Device a",5,"Temp+Hum",DeviceID="00:0a:95:9d:68:16").Create()
        #Domoticz.Device("Device b",4,"Barometer",DeviceID="00:0a:95:9d:68:16").Create()
        #Domoticz.Device("Device c",3,"Text",DeviceID="00:0a:95:9d:68:16").Create()
        #Domoticz.Device("Device d",42,"Text",DeviceID="00:0a:95:9d:68:18").Create()
        #Domoticz.Device("Device e",7,"Text",DeviceID="00:0a:95:9d:68:25").Create()
        
        DumpConfigToLog()

        sAddress, sep, sPort = Parameters["Mode1"].partition(':')
        self.BeaconConn = Domoticz.Connection(Name="Beacon",
                Transport="UDP/IP", Address=sAddress, Port=str(sPort))
        self.BeaconConn.Listen()

    def onMessage(self, Connection, Data):
        try:
            strMessage = Data.decode("utf-8", "ignore")
            Domoticz.Log("onMessage called from: "+Connection.Address+":"+Connection.Port+" with data: "+strMessage)
            
            # decode MySensors message
            mySensorsMsg = MySensorsMessage(strMessage)
            Domoticz.Log(repr(mySensorsMsg))
            
            # process supported messages
            if mySensorsMsg.isValid():
                if(int(mySensorsMsg.cmd) == const.MessageType.internal):
                    processInternalMsg(mySensorsMsg,Connection)
                elif (int(mySensorsMsg.cmd) == const.MessageType.presentation):
                    processPresentationMsg(mySensorsMsg,Connection)
                elif (int(mySensorsMsg.cmd) == const.MessageType.set):
                    processSetMsg(mySensorsMsg,Connection)
                else:
                    if mySensorsMsg.isValid():
                        Domoticz.Log("Unsupported message!")
                    else:
                        Domoticz.Log("Not valid MySensors message!")
                    
            # debug what we did to devices
            #DumpConfigToLog()
        except Exception as inst:
            Domoticz.Error("Exception in onMessage, called with Data: '"+str(strMessage)+"'")
            Domoticz.Error("Exception detail: '"+str(inst)+"'")
            raise

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

#############################################################################
#                MySensors message processing functions                     #
#############################################################################
def processInternalMsg(mySensorsMsg,Connection):
    Domoticz.Log("Processing internal message...")
    if int(mySensorsMsg.cmdType) == const.Internal.I_ID_REQUEST:
        Domoticz.Log("->I_ID_REQUEST recived...")
        # payload should have unique ID (MAC ADDRESS)
        uniqueID = mySensorsMsg.payload
        # check if uniqueID is already present on the system
        nodeID = getNodeID(uniqueID)
        Domoticz.Log("NodeID " + str(nodeID) + " assigned...")
        # send nodeID back
        responseMsg = MySensorsMessage()
        responseMsg.createMsg(0, 0, int(const.MessageType.internal), 0, int(const.Internal.I_ID_RESPONSE), nodeID)
        sendUDPMessage(Connection,responseMsg)
    else:
        Domoticz.Log("Unsupported request recived!")

def processPresentationMsg(mySensorsMsg,Connection):
    Domoticz.Log("Processing presentation message...")
    if int(mySensorsMsg.cmdType) == const.Presentation.S_BARO:
        # Barometer device
        Domoticz.Log("Barometer device reported...")
        pass
    elif int(mySensorsMsg.cmdType) == const.Presentation.S_HUM:
        # Humudity device
        Domoticz.Log("Humidity device reported...")
        pass
    elif int(mySensorsMsg.cmdType) == const.Presentation.S_TEMP:
        # Temperature device
        Domoticz.Log("Temperature device reported...")
        pass
    else:
        # Curently not supported device
        Domoticz.Log("Device not supported!")

def processSetMsg(mySensorsMsg,Connection):
    Domoticz.Log("Processing set message...")
    pass

#############################################################################
#                           UDP helper functions                            #
#############################################################################

def sendUDPMessage(Connection, mySensorsMsg):
    # try sending response over UDP
    Domoticz.Log("Send to: "+Connection.Address+":"+Connection.Port+" data: "+mySensorsMsg)
    Connection.Send(str(mySensorsMsg))
            
#    if (Parameters["Mode2"] == "True"):
#        existingDevice = 0
#        existingName = (Parameters["Name"]+" - "+Connection.Address)
#        for dev in Devices:
#            if (Devices[dev].Name == existingName):
#                existingDevice = dev
#        if (existingDevice == 0):
#            Domoticz.Device(Name=Connection.Address, Unit=len(Devices)+1, TypeName="Text", Image=17).Create()
#            Domoticz.Log("Created device: "+Connection.Address)
#            Devices[len(Devices)].Update(nValue=1,
#                    sValue=Connection.Address+';'+strData)
#        else:
#            Devices[existingDevice].Update(nValue=1,
#                    sValue=Connection.Address+';'+strData)
 
#############################################################################
#                         Domoticz helper functions                         #
#############################################################################

# Update Device into database
def UpdateDevice(Unit, nValue, sValue, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or AlwaysUpdate == True:
            Devices[Unit].Update(nValue, str(sValue))
            Domoticz.Log("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")
    return

# Create device
def CreateDevice():
    pass

# Report new / current nodeID depending on uniqueID
def getNodeID(uniqueID):
    foundUnits = []
    for x in Devices:
        if Devices[x].DeviceID == uniqueID:
            foundUnits.append(x)
    if len(foundUnits) > 0:
        return min(foundUnits)
    else:
        if len(Devices) > 0:
            return max(Devices)+1
        else:
            return 1

# Dump configuration to log
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Log( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Log("Device count: " + str(len(Devices)))
    if len(Devices) > 0 : Domoticz.Log("Highest Unit: " + str(max(Devices)))
    for x in Devices:
        Domoticz.Log("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Log("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Log("Device HwID:     '" + str(Devices[x].DeviceID) + "'")
        Domoticz.Log("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Log("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Log("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Log("Device LastLevel: " + str(Devices[x].LastLevel))
    return
