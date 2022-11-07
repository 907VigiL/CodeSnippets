import re
from socket import*
from bitstring import BitArray, Bits

class TCPSegment:
    segLen = 1500 - 20 - 8
    headerWords = 5
    headerLen = headerWords * 4
    dataLen = segLen - headerLen

    def __init__(self, data, srcPort, destPort, seqNum = 0, ackNum = 0, window = 1472, isAck = False, isSynch = False, isFin = False): 
        if len(data) > self.dataLen:
            raise ValueError("Data length of " + str(len(data)) + "exceeds max of " + str(self.dataLen))
        if srcPort >= 2 ** 16:
            raise ValueError("Source Port too high")
        if destPort >= 2 ** 16:
            raise ValueError("Destination Port too high")
        if window >= 2 ** 16:
            raise ValueError("Window too large")
        if srcPort < 0 or destPort < 0 or seqNum < 0 or ackNum < 0 or window < 0:
            raise ValueError("Negative numbers are not allowed")
        self.data = data
        self.srcPort, self.destPort = srcPort, destPort
        self.seqNum, self.ackNum = seqNum % (2 ** 32), ackNum % (2 ** 32)
        self.window = window
        self.isAck, self.isSynch, self.isFin = isAck, isSynch, isFin


    def toBytes(self):
        num = 0
        array = BitArray(self.srcPort.to_bytes(2, "big") + self.destPort.to_bytes(2, "big")
		               + self.seqNum.to_bytes(4, "big") + self.ackNum.to_bytes(4, "big")
		               + b"\0\0" + self.window.to_bytes(2, "big") + b"\0\0\0\0" + self.data) #Assemble segment.
        array[96:100] = Bits(self.headerWords.to_bytes(1, "big"))[4:8] #Set data offset bits.
        array[107], array[110], array[111] = self.isAck, self.isSynch, self.isFin #Set control bits.
        array[128:144] = Bits(num.to_bytes(2, "big")) #Sets checksum to all 0's
        return array.tobytes()

        
    def setWindow(self, window):
        self.window = window
        self.toBytes()

        
    def buildPacket(self, data, seqNum, ackNum):
        self.data = data
        self.seqNum = seqNum
        self.ackNum = ackNum
        return self.toBytes()

        
    def buildSynchPacket(self, seqNum):
        self.isSynch = True
        self.seqNum = seqNum
        return self.toBytes()
        

    def buildAckPacket(self, data, seqNum, ackNum):
        self.isAck = True
        self.seqNum = seqNum
        self.ackNum = ackNum
        self.data = data
        return self.toBytes()

    def buildNoDataAckPacket(self, seqNum, ackNum):
        self.isAck = True
        self.seqNum = seqNum
        self.ackNum = ackNum
        return self.toBytes()


    def buildFinPacket(self, seqNum, ackNum):
        self.isFin = True
        self.isAck = True
        self.seqNum = seqNum
        self.ackNum = ackNum
        return self.toBytes()
        

def openHeader(segment):
        serverPort = int.from_bytes(segment[0:16].tobytes(), "big")
        clientPort = int.from_bytes(segment[16:32].tobytes(), "big")
        seqNum = int.from_bytes(segment[32:64].tobytes(), "big")
        ack = int.from_bytes(segment[64:96].tobytes(), "big")
        window = int(int.from_bytes(segment[112:128].tobytes(), "big"))
        return serverPort, clientPort, seqNum, ack, window