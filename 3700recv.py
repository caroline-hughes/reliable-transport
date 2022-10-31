#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math

class Receiver:
    # dict mapping seqnum -> msg, for packets recieved out of order
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
        print(msg["data"], end='', flush=True) # print
        self.send({ "type": "ack", "seqnum": seqnum }) # send the ack
        self.seen.append(seqnum) # append it to list of seen seq nums
        self.expected_seqnum += 1 # increment

    def check_next_ack(self):
        next_ack = self.stored_data.get(self.expected_seqnum)
        if next_ack is not None:
            self.send_ack(next_ack, self.expected_seqnum)
            self.check_next_ack() # call recursive check for next acks 
        else:
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

                # if next seq number
                self.log('if seqnum == self.expected_seqnum: '+ str(seqnum) + '==' + str(self.expected_seqnum) + '?')
                if seqnum == self.expected_seqnum:
                    self.send_ack(msg, seqnum)
                    self.check_next_ack()

                # if duplicate seq number 
                elif seqnum in self.seen:
                    self.log("got duplicate packet %s \n" % str(seqnum))

                # if out of order
                else:
                    self.log("got out of order packet %s \n" % str(seqnum))
                    # save the datagram to the dict, don't ack yet
                    self.stored_data[seqnum] = msg
                    
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='receive data')
    args = parser.parse_args()
    sender = Receiver()
    sender.run()
