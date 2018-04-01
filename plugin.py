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

class BasePlugin:
    BeaconConn = None

    def __init__(self):
        return

    def onStart(self):
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
class MySensorsMessage:
    nodeID = None
    sensorID = None
    cmd = None
    ack = None
    cmdType = None
    payload = None
    
    def __init__(self,strMessage=None):
        try:
            self.nodeID,self.sensorID,self.cmd,self.ack,self.cmdType,self.payload = strMessage.split(';')
        except ValueError:
            # not valid message
            self.nodeID = None
            self.sensorID = None
            self.cmd = None
            self.ack = None
            self.cmdType = None
            self.payload = None
        return
    
    def isValid(self):
        # return true if all values are not None = true
        return all([self.nodeID,self.sensorID,self.cmd,self.ack,self.cmdType,self.payload])
    
    def createMsg(self,nodeID,sensorID,cmd,ack,cmdType,payload):
        self.nodeID = str(nodeID)
        self.sensorID = str(sensorID)
        self.cmd = str(cmd)
        self.ack = str(ack)
        self.cmdType = str(cmdType)
        self.payload = str(payload)
    
    def __repr__(self):
        # string representation used for debugging
        if self.isValid():
            strData  = "MySensors message: \n"
            strData += "nodeID: " + str(self.nodeID) + "\n"
            strData += "child-sensor-id: " + str(self.sensorID) + "\n"
            strData += "command: " + str(self.cmd) + "\n"
            strData += "Ack?: " + str(self.ack) + "\n"
            strData += "Type: " + str(self.cmdType) + "\n"
            strData += "Payload: " + str(self.payload) + "\n"
        else:
            strData  = "Unknown message!"
        return strData
    
    def __str__(self):
        # string representation used for sending messages
        if self.isValid():
            strData  = str(self.nodeID) + ";"
            strData += str(self.sensorID) + ";"
            strData += str(self.cmd) + ";"
            strData += str(self.ack) + ";"
            strData += str(self.cmdType) + ";"
            strData += str(self.payload)
        else:
            strData  = ""
        return strData

def processInternalMsg(mySensorsMsg,Connection):
    Domoticz.Log("Processing internal message...")
    if int(mySensorsMsg.cmdType) == const.Internal.I_ID_REQUEST:
        Domoticz.Log("->I_ID_REQUEST recived...")
        # payload should have unique ID (MAC ADDRESS)
        uniqueID = mySensorsMsg.payload
        # check if uniqueID is already present on the system
        # nodeID = getNodeID(uniqueID)
        # send nodeID back
        responseMgs = MySensorsMessage.createMsg(0,0,const.MessageType.internal,0,const.Internal.I_ID_RESPONSE,nodeID)
        sendUDPMessage(Connection,responseMgs)
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
    pass

# Dump configuration to log
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
