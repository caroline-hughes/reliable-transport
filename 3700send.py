#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math, datetime
from re import L

DATA_SIZE = 1375
WINDOW_SIZE = 4

class Sender:

    # seqnum -> time sent
    awaiting_ack = {}

    packs = {}

    next_seqn = 0  # what we give a new packet thats being sent
    curr_acks = 0  # for window

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

    def check_timeouts(self):
        for k in self.awaiting_ack.keys():
            now = time.time()
            diff = now - self.awaiting_ack.get(k)
            # self.log("FOR KEY: %s" % k)
            # self.log("TIME DIFF: %s" % str(diff))
            if diff > 2:
                self.log("FOR KEY: %s" % k)
                self.log("TIME DIFF: %s" % str(diff))
                self.retransmit(k)

    def retransmit(self, k):
        self.log("RETRANSMITTING seqnum '%s'" % str(k))
        msg = self.packs.get(k)
        self.send(msg)
        self.awaiting_ack[k] = time.time()
        return
        
    def run(self):
        
        while True:
            sockets = [self.socket, sys.stdin] if not self.waiting else [self.socket]

            socks = select.select(sockets, [], [], 0.1)[0]

            self.check_timeouts()

            for conn in socks:
                if conn == self.socket:
                    # check if its been over a sec waiting for any youve sent

                    k, addr = conn.recvfrom(65535) # get an ack
                    msg = json.loads(k.decode('utf-8'))
                    self.log("Received message '%s'" % msg)
                    acked_seqnum = msg["seqnum"]

                    self.log("got ack for '%s'" % acked_seqnum)
                    self.awaiting_ack.pop(acked_seqnum)

                    if self.curr_acks == WINDOW_SIZE - 1:
                        self.waiting = False # done waiting
                        self.curr_acks = 0
                    else:
                        self.curr_acks += 1

                elif conn == sys.stdin: # read more data from stdin
                    for n in range(WINDOW_SIZE):
                        data = sys.stdin.read(DATA_SIZE)
                        
                        if len(data) == 0 and (len(self.awaiting_ack) == 0):
                            self.log("All done!")
                            sys.exit(0)

                        msg = { "type": "msg", "seqnum": self.next_seqn, "data": data}
                        self.log("Sending message '%s'" % msg)
                        self.send(msg)
                        self.awaiting_ack[self.next_seqn] = time.time()
                        self.packs[self.next_seqn] = msg
                        self.next_seqn += 1

                    self.waiting = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='send data')
    parser.add_argument('host', type=str, help="Remote host to connect to")
    parser.add_argument('port', type=int, help="UDP port number to connect to")
    args = parser.parse_args()
    sender = Sender(args.host, args.port)
    sender.run()


    # def got_all_acks(self, acks, seqnum):
    #     for i in range(seqnum):
    #         if acks[i] != 1:
    #             return False
    #     return True