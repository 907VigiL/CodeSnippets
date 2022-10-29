
import argparse
import time
import sys
import os
from os import listdir
from os.path import isfile, join
from socket import *

CONNECTION_TIMEOUT = 10
#ArgParse
parser = argparse.ArgumentParser()
parser.add_argument("-a", "--address", help = "IP Address", type = str, required = True)
parser.add_argument("-sp", "--serverPort", help = "Server port", type = int, required = True)
parser.add_argument("-f", "--filename", help = "File name", type = str, required = True)
parser.add_argument("-p", "--portNumber", help = "Port numbers", type = int, required = True)
parser.add_argument("-m", "--mode", help = "Mode; r = read from server, w = write to server", type = str, required = True)
args = parser.parse_args()

#Check Argument
if not 5000 <= args.serverPort < 65535:
    print("Error: -sp should be in range 5000-65535. You entered", args.serverPort)
    exit()
if not 5000 <= args.portNumber < 65535:
    print("Error: -p should be in range 5000-65535. You entered", args.portNumber)
    exit()
if args.mode != 'r' and args.mode != 'w':
    print("Error: invalid mode input. Must be r or w.")
    exit()
time.sleep(1)

#Open UPD
serverAddress = args.address
serverPortNum = args.serverPort
TID = (serverAddress, serverPortNum)
clientPort = args.portNumber
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(CONNECTION_TIMEOUT)

#Send RRQ\WRQ
#build packet
rqPacket = bytearray()
rqPacket.append(0)
if args.mode == 'r':
    rqPacket.append(1) # if mode is read
else:
    rqPacket.append(2) # if mode is write
#filename
fileName = bytearray(args.filename, 'utf-8')
rqPacket += fileName
rqPacket.append(0)
#transfer mode
transferMode = bytearray(bytes('netascii','utf-8'))
rqPacket += transferMode
rqPacket.append(0)
#send file
clientSocket.sendto(rqPacket, (serverAddress, serverPortNum))

#Send Data
def packData(dataIn, filIn):
    DATPacket = bytearray(dataIn)
    DATPacket[0] = 0
    DATPacket[1] = 3
    #get block num and increment
    blockNum = dataIn[2:4]
    blockInt = int.from_bytes(blockNum, byteorder = 'big')
    blockInt += 1
    if blockInt > 65535:
        blockInt = 0
    DATPacket[2:4] = blockInt.to_bytes(2, 'big')
    #add datapacks
    f = filIn
    byte = f.read(1)
    while byte != b"":
        DATPacket += byte
        if len(DATPacket) == 516:
            break
        byte = f.read(1)
    return DATPacket

#Send ACK
def packAcknowledgement(dataIn):
    ACKPacket = bytearray(dataIn)
    ACKPacket[0] = 0
    ACKPacket[1] = 4
    if int.from_bytes(ACKPacket[2:4], byteorder = 'big') > 65535:
        backToZero = 0
        ACKPacket[2:4] = int.to_bytes(backToZero, byteorder = 'big')
    return ACKPacket

#Recv ERR
def recieveErr(dataIn):
    errCode = str(int.from_bytes(dataIn[:2], byteorder = 'big')) #needs to convert to string for errOutput
    errMsg = dataIn[4:].decode()
    errOutput = "Error: " + errCode + ' ' + errMsg
    return errOutput

#Send Error
def sendErr(errCode, errMsg):
    if errCode == 0:
        errMsg = "Not defined, see error message (if any)."
    elif errCode == 1: 
        errMsg = "File not found."
    elif errCode == 2: 
        errMsg = "Access violation."
    elif errCode == 3: 
        errMsg = "Disk full or allocation exceeded."
    elif errCode == 4: 
        errMsg = "Illegal TFTP operation."
    elif errCode == 5: 
        errMsg = "Unknown transfer ID."
    elif errCode == 6: 
        errMsg = "File already exists."
    elif errCode == 7: 
        errMsg = "No such user."

    ErrPacket = bytearray(errCode)
    ErrPacket[0] = 0
    ErrPacket[1] = 5
    ErrPacket.append(errMsg)
    ErrPacket.append(0)



#WRQ Connection
 
if args.mode == 'w':
    currSequence = 0
    file = open(args.filename, 'rb')
    while True:
        data, serverAddress = clientSocket.recvfrom(516)
        if serverAddress != TID:
            print("Received a file from unknown TID")
            continue
        currAck = int.from_bytes(data[2:4], byteorder = 'big')
        if currSequence > 65535:
            currSequence = 0
        if currAck == currSequence:
            currSequence += 1
            packSend = packData(data[0:4], file)
            clientSocket.sendto(packSend, serverAddress)
            tempPack = packSend
        else:
            clientSocket.sendto(tempPack, serverAddress)
        if len(packSend) < 516:
            file.close()
            clientSocket.close()
            break
        if(int.from_bytes(data[0:2], 'big') == 5):
            errMsg = recieveErr(data)
            print(errMsg)
            file.close()
            clientSocket.close()
            break

   
#RRQ Connection
if args.mode == 'r':
    file = open(args.filename, 'wb')
    currSequence = 1
    while True:
        data, serverAddress = clientSocket.recvfrom(516)
        if serverAddress != TID:
            print("Received a file from unknown TID")
            continue
        if(int.from_bytes(data[0:2], 'big') == 5):
            errMsg = recieveErr(data)
            print(errMsg)
            break
        #check if ack packet is = sequence number
        packetToSend = packAcknowledgement(data[0:4])
        currAck = int.from_bytes(packetToSend[2:4], byteorder = 'big')
        if currSequence > 65535:
            currSequence = 0
        # if it isn't, resend the ACK packet we are stuck on
        if currAck != currSequence:
            clientSocket.sendto(packetToSend, serverAddress)
        # if it is, continue as normal
        else:
            currSequence += 1
            clientSocket.sendto(packetToSend, serverAddress)
            readIn = data[4:]
            #print(readIn)
            file.write(readIn)
            if len(data[4:]) < 512:
                file.close()
                clientSocket.close()
                break
        if(int.from_bytes(data[0:2], 'big') == 5):
            errMsg = recieveErr(data)
            print(errMsg)
            break

clientSocket.close()
exit()