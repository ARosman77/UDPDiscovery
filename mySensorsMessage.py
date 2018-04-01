"""MySensors message class for version 2.0 of MySensors."""
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
        except (ValueError, AttributeError):
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