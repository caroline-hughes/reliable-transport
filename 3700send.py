#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math, datetime
from re import L

DATA_SIZE = 1375
WINDOW_SIZE = 4

class Sender:

    # seqnum -> time sent
    sent = {}

    # seqnum -> msg
    packs = {}

    # seqnum -> bool
    acked = {}

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

    # def got_all_acks(self, acks, seqnum):
    #     for i in range(seqnum):
    #         if acks[i] != 1:
    #             return False
    #     return True

    def run(self):
        seqnum = 1
        expected_ack_seqnum = 1
        curr_acks = 0

        while True:
            sockets = [self.socket, sys.stdin] if not self.waiting else [self.socket]

            socks = select.select(sockets, [], [], 0.1)[0]

            for k in self.sent.keys():
                now = time.time()
                diff = now - self.sent.get(k)
                #self.log("FOR KEY: %s" % k)
                #self.log("TIME DIFF: %s" % str(diff))
                if diff > 2:
                    self.log("FOR KEY: %s" % k)
                    self.log("TIME DIFF: %s" % str(diff))
                    self.retransmit(k)

            for conn in socks:
                if conn == self.socket:
                    # check if its been over a sec waiting for any youve sent

                    k, addr = conn.recvfrom(65535) # get an ack
                    msg = json.loads(k.decode('utf-8'))
                    self.log("Received message '%s'" % msg)
                    the_seqnum = msg["seqnum"]

                    if the_seqnum == expected_ack_seqnum:
                        self.log("got expected seqnum '%s'" % the_seqnum)
                        self.sent.pop(the_seqnum)
                        expected_ack_seqnum += 1
                        if curr_acks == WINDOW_SIZE - 1:
                            self.waiting = False # done waiting
                            curr_acks = 0
                        else:
                            curr_acks += 1
                    
                    else:
                        self.log("got out of order seqnum '%s'" % the_seqnum)


                elif conn == sys.stdin: # read more data from stdin
                    for n in range(WINDOW_SIZE):
                        data = sys.stdin.read(DATA_SIZE)
                        
                        if len(data) == 0:
                            self.log("All done!")
                            sys.exit(0)

                        msg = { "type": "msg", "seqnum": seqnum, "try":  1, "data": data}
                        self.log("Sending message '%s'" % msg)
                        self.send(msg)
                        self.sent[seqnum] = time.time()
                        self.packs[seqnum] = msg
                        seqnum += 1

                    self.waiting = True

        return
    
    def retransmit(self, k):
        self.log("lost packet. RETRANSMITTING")
        # self.log("Retransmitting seqnum '%s'" % str(k))
        msg = self.packs.get(k)
        msg["try"] = msg["try"] + 1
        self.send(msg)
        self.sent[k] = time.time()
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='send data')
    parser.add_argument('host', type=str, help="Remote host to connect to")
    parser.add_argument('port', type=int, help="UDP port number to connect to")
    args = parser.parse_args()
    sender = Sender(args.host, args.port)
    sender.run()
