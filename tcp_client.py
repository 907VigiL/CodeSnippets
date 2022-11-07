from socket import*
import argparse 
from TCPSegment import*
from TCPStateMachine import*
from bitstring import Bits, BitArray
from statemachine import StateMachine, State

parser = argparse.ArgumentParser(description="Uses TCP to send or recieve files")
parser.add_argument("-m", "--mode", help = "mode of eitehr writing or reading", required = True, type = str)
parser.add_argument("-a", "--address", help = "remote host / server to communicate with", required = True, type = str)
parser.add_argument("-cp", "--clientPort", help = "Get Client Port", required = True, type = int)
parser.add_argument("-sp", "--serverPort", help ="input server port", required = True, type = int)
parser.add_argument("-f", "--filename", help = "input file name", required = True, type = str)
args = parser.parse_args()
if  args.serverPort < 5000 or args.serverPort > 65535:
    print("Error: -sp should be in range 5000-65535. You entered", args.serverPort)
    exit()

elif args.clientPort < 5000 or args.clientPort > 65535:
    print("Error: -p should be in range 5000-65535. You entered", args.portNumber)
    exit()

elif args.mode != 'r' and args.mode != 'w':
    print("Error: invalid mode input. Must be r or w.")
    exit()

else:
    ipAddress = args.address
    clientPort = args.clientPort
    serverPort = args.serverPort
    file = args.filename
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.bind(("", clientPort))
    clientSocket.connect((ipAddress, serverPort))
    data = b'\0'
    firstAck = 0
    oldAckNum = 0

    try:
        states = TCPState()
        states.activeOpen()

        #while loop serves as listen
        while(not states.is_closed):

            if(states.is_synchSent):
                if(args.mode == 'w'):
                    f = open(file, 'rb')
                else:
                    f = open(file, 'wb')
                #start of handshake
                segmentToSend = TCPSegment(data = b'', srcPort = clientPort, destPort = serverPort)
                synchSegment = segmentToSend.buildSynchPacket(0)   
                clientSocket.sendall(synchSegment)

                clientSocket.settimeout(8)
                recvdSegment = clientSocket.recv(2000)
                recvdSegment = BitArray(recvdSegment)
                serverPort, clientPort, seqNum, ackNum, myWindow = openHeader(recvdSegment)
                segmentToSend = TCPSegment(data = b'', srcPort = clientPort, destPort = serverPort)
                segmentToSend.setWindow(myWindow)

                if(recvdSegment[107] and recvdSegment[110]):
                    segmentToSend = segmentToSend.buildAckPacket(b'', ackNum, seqNum + 1)
                    clientSocket.sendall(segmentToSend)
                    states.rcvAckSynch()#sends to estab
                
                elif(recvdSegment[110]):
                    segmentToSend = segmentToSend.buildAckPacket(b'', ackNum, seqNum + 1)
                    clientSocket.sendall(segmentToSend)
                    states.rcvSynch()#sends to synchRcvd

            #this is never used as our client is never the one recieving the first segment but is still written for completeness
            elif(states.is_synchRcvd):
                clientSocket.settimeout(8)
                recvdSegment = clientSocket.recv(2000)
                recvdSegment = BitArray(recvdSegment)
                serverPort, clientPort, seqNum, ackNum, myWindow = openHeader(recvdSegment)
                segmentToSend = TCPSegment(data = b'', srcPort = clientPort, destPort = serverPort)
                segmentToSend.setWindow(myWindow)
                if(recvdSegment[107]):
                    states.rcvAckofSynch()#sends to estab
                else:
                    segmentToSend = segmentToSend.buildFinPacket(ackNum, seqNum)
                    clientSocket.sendall(segmentToSend)
                    states.closeState()#sends to finWait1
                    
            elif(states.is_estab):
                clientSocket.settimeout(8)
                recvdSegment = clientSocket.recv(2000)
                recvdSegment = BitArray(recvdSegment)
                serverPort, clientPort, seqNum, ackNum, myWindow = openHeader(recvdSegment)
                segmentToSend = TCPSegment(data = b'', srcPort = clientPort, destPort = serverPort)
                segmentToSend.setWindow(myWindow)
                #check fin bit    
                if(recvdSegment[111]):
                    segmentToSend = segmentToSend.buildAckPacket(b'', ackNum, seqNum)
                    clientSocket.sendall(segmentToSend)
                    states.rcvFin()#sends to close wait

                else:
                    if(args.mode == 'r'):
                        #uses offset to move to data payload of segment
                        offset = recvdSegment[96:100].tobytes()
                        header =  int(int.from_bytes(offset, 'big')/16)
                        data = recvdSegment[(header*32):].tobytes()
                        segmentToSend = segmentToSend.buildNoDataAckPacket(ackNum, seqNum + len(data))
                        clientSocket.sendall(segmentToSend)
                        if(len(data) != 0):
                            f.write(data) #this took me forever because I forgot we had to write it to our own file for it to be read!
                        else:
                            states.rcvFin()#sends to closeWait

                    elif(args.mode == 'w'):
                        data = f.read(1452)
                        if(ackNum == oldAckNum):
                            failedToSend = True

                        if(len(data) == 0):
                            segmentToSend = segmentToSend.buildFinPacket(ackNum, seqNum)
                            clientSocket.sendall(segmentToSend)
                            states.closeState()#sends to finWait1

                        #would be used to check if packet got dropped and resend could never fully implement
                        elif(failedToSend):
                            segmentToSend = segmentToSend.buildPacket(data, ackNum, seqNum + len(data))
                            clientSocket.sendall(segmentToSend)

                        elif(firstAck == 1):    
                            segmentToSend = segmentToSend.buildPacket(data, ackNum, seqNum + len(data))
                            clientSocket.sendall(segmentToSend)

                        elif(firstAck == 0):
                            segmentToSend = segmentToSend.buildAckPacket(data, ackNum, seqNum + len(data))
                            clientSocket.sendall(segmentToSend)
                            firstAck = 1

            elif(states.is_finWait1):
                clientSocket.settimeout(8)
                recvdSegment = clientSocket.recv(2000)
                recvdSegment = BitArray(recvdSegment)
                serverPort, clientPort, seqNum, ackNum, myWindow = openHeader(recvdSegment)
                segmentToSend = TCPSegment(data = b'', srcPort = clientPort, destPort = serverPort)
                segmentToSend.setWindow(myWindow)
                    
                if(recvdSegment[107] and recvdSegment[111]):
                    states.rcvAckofFin()#sends to finWait2
                    
                if(recvdSegment[107] and not recvdSegment[111]):
                    clientSocket.close()
                    exit()

                if(recvdSegment[111] and not recvdSegment[107]):
                    segmentToSend = segmentToSend.buildAckPacket(b'', ackNum, seqNum + 1)
                    clientSocket.sendall(segmentToSend)
                    states.rcvFin()#sends to closing

            elif(states.is_finWait2):
                clientSocket.settimeout(8)
                segmentToSend = TCPSegment(data = b'', srcPort = clientPort, destPort = serverPort)
                segmentToSend.setWindow(myWindow)
                segmentToSend = segmentToSend.buildAckPacket(b'', ackNum, seqNum + 1)
                clientSocket.sendall(segmentToSend)
                states.rcvFin()#sends to timeWait

            elif(states.is_closeWait):
                segmentToSend = TCPSegment(data = b'', srcPort = clientPort, destPort = serverPort)
                segmentToSend.setWindow(myWindow)
                segmentToSend = segmentToSend.buildFinPacket(ackNum, seqNum)
                clientSocket.sendall(segmentToSend)
                states.closeState()#send to lastAck

            elif(states.is_lastAck):
                clientSocket.settimeout(8)
                recvdSegment = clientSocket.recv(2000)
                recvdSegment = BitArray(recvdSegment)
                states.rcvAckofFin()#send to closed

            elif(states.is_closing):
                states.rcvAckofFin()#sends to timeWait

            elif(states.is_timeWait):
                #would normally have double MSL time here but dont want program to wait that long
                states.timeWaitClose()#sends to closed

        f.close()
        clientSocket.close()
        exit()

    except Exception as e:
        print("Encountered an Unknown Error: ", e , "\n")
    finally:
            print("Exiting\n")
            exit()