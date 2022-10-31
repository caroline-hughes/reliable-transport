#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math

class Receiver:
    # dict mapping seqnum -> msg
    stored_data = {}
    expected_seqnum = 1
    seen = []

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 0))
        self.port = self.socket.getsockname()[1]
        self.log("Bound to port %d" % self.port)

        self.remote_host = None
        self.remote_port = None

    def send(self, message):
        self.socket.sendto(json.dumps(message).encode('utf-8'), (self.remote_host, self.remote_port))

    def log(self, message):
        sys.stderr.write(message + "\n")
        sys.stderr.flush()

    def send_ack(self, msg, seqnum):
        self.log('sending ack for seqn %s' % seqnum)
        print(msg["data"], end='', flush=True) 
        self.send({ "type": "ack", "seqnum": seqnum }) 
        # self.seen.append(seqnum) 

    def check_next_ack(self):
        # next_ack = self.stored_data.get(self.expected_seqnum)
        # if next_ack is not None:
        #     self.send_ack(next_ack, self.expected_seqnum)
        #     self.expected_seqnum += 1 # increment
        #     self.check_next_ack() # call recursive check for next acks 
        # else:
        return

    def run(self):
        while True:
            socks = select.select([self.socket], [], [])[0]
            for conn in socks:
                data, addr = conn.recvfrom(65535)

                # Grab the remote host/port if we don't already have it
                if self.remote_host is None:
                    self.remote_host = addr[0]
                    self.remote_port = addr[1]

                msg = json.loads(data.decode('utf-8'))
                self.log("Received data message %s" % msg)

                seqnum = msg["seqnum"] # get packet seq number
                curr_try = msg["try"]
                
                self.log("expected next packet for %s \n" % str(self.expected_seqnum))
                # check if we've gotten a version of this packet before
                existing = self.stored_data.get(seqnum)
                if existing is not None: # got a duplicate
                    if seqnum < self.expected_seqnum:
                        self.log("got duplicate packet %s \n" % str(seqnum))
                        if curr_try > existing["try"]: # its a retransmission, ack it
                            self.log("but its a newer version \n")
                            self.send_ack(msg, seqnum)
                            self.expected_seqnum = seqnum + 1   # reset expected
                elif seqnum == self.expected_seqnum: # got the next expected
                        self.send_ack(msg, seqnum)
                        self.expected_seqnum += 1 # increment
                        self.check_next_ack()
                else: # got an out of order ack
                    self.log("got out of order packet %s \n" % str(seqnum))
                    # ack???
                
                # save the datagram to the dict
                self.stored_data[seqnum] = msg
                    
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='receive data')
    args = parser.parse_args()
    sender = Receiver()
    sender.run()
