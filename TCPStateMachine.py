from statemachine import StateMachine, State

class TCPState(StateMachine):
    synchSent = State('Synch-Sent')
    synchRcvd = State('Synch-Rec')
    estab     = State('Establish1')
    finWait1  = State('Fin-Wait-1')
    finWait2  = State('Fin-Wait-2')
    closeWait = State('Close-Wait')
    closing   = State('Closing')
    lastAck   = State('Last-Ack')
    timeWait  = State('Time-Wait')
    closed    = State('Closed', initial = True)

    rcvSynch = synchSent.to(synchRcvd) 

    rcvAckSynch = synchSent.to(estab)

    rcvAckofSynch = synchRcvd.to(estab)

    closeState = synchRcvd.to(finWait1) | estab.to(finWait1) | closeWait.to(lastAck) | synchSent.to(closed) 

    activeOpen = closed.to(synchSent)

    rcvFin = estab.to(closeWait) | finWait1.to(closing) | finWait2.to(timeWait)

    rcvAckofFin = finWait1.to(finWait2) | closing.to(timeWait) | lastAck.to(closed)

    timeWaitClose = timeWait.to(closed)    