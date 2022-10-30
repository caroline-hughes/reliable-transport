#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math

DATA_SIZE = 1375

class Sender:
    def __init__(self, host, port):
        self.host = host
        self.remote_port = int(port)
        self.log("Sender starting up using port %s" % self.remote_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 0))
        self.waiting = False

    def log(self, message):
        sys.stderr.write(message + "\n")
        sys.stderr.flush()

    def send(self, message):
        self.socket.sendto(json.dumps(message).encode('utf-8'), (self.host, self.remote_port))

    def run(self):
        seqnum = 1
        expected_ack_seqnum = 1

        curr_acks = 0
        while True:
            sockets = [self.socket, sys.stdin] if not self.waiting else [self.socket]

            socks = select.select(sockets, [], [], 0.1)[0]

            for conn in socks:
                if conn == self.socket:
                    k, addr = conn.recvfrom(65535) # get an ack
                    msg = json.loads(k.decode('utf-8'))
                    acked_seqnum = msg["seqnum"]
                    if expected_ack_seqnum == acked_seqnum:
                        self.log("GOT EXPECTED ACK: '%s'" % str(acked_seqnum))
                        expected_ack_seqnum += 1
                        
                        # if second ack
                        if curr_acks == 1:
                            self.waiting = False # done waiting
                            curr_acks = 0
                        else:
                            curr_acks += 1
                    else:
                        self.log("GOT UNEXP ACK: '%s'" % str(acked_seqnum))

                    self.log("Received message '%s'" % msg)
                    
                elif conn == sys.stdin: # if got an ack, read more data from stdin

                    # send first
                    data1 = sys.stdin.read(DATA_SIZE)
                    
                    if len(data1) == 0:
                        self.log("All done!")
                        sys.exit(0)

                    
                    msg1 = { "type": "msg", "seqnum": seqnum, "data": data1 }
                    self.log("Sending message '%s'" % msg1)
                    self.send(msg1)
                    seqnum+=1

                    # send second
                    data2 = sys.stdin.read(DATA_SIZE)
                    if len(data2) == 0:
                        self.log("All done!")
                        sys.exit(0)

                    msg2 = { "type": "msg", "seqnum": seqnum, "data": data2 }
                    self.log("Sending message '%s'" % msg2)
                    self.send(msg2)
                    seqnum+=1

                    self.waiting = True

        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='send data')
    parser.add_argument('host', type=str, help="Remote host to connect to")
    parser.add_argument('port', type=int, help="UDP port number to connect to")
    args = parser.parse_args()
    sender = Sender(args.host, args.port)
    sender.run()
