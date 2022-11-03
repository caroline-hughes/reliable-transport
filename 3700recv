#!/usr/bin/env -S python3 -u

import argparse, socket, time, json, select, struct, sys, math, zlib
from json import JSONDecodeError


class Receiver:
    acked = {}
    seqn_to_print = 0  # keeps track of which packet to print next

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
        self.send({ "type": "ack", "seqnum": seqnum }) 
        self.acked[seqnum] = msg

    def print_recursive(self, msg):
        print(msg["data"], end='', flush=True)
        self.seqn_to_print += 1
        # check if next is in to_print: weve already acked it but havent yet printed
        next_to_print = self.acked.get(self.seqn_to_print)
        if next_to_print is not None:
            self.print_recursive(next_to_print)
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

                try:
                    msg = json.loads(data.decode('utf-8'))
                    self.log("Received data message %s" % msg)
                    seqnum = msg["seqnum"]

                    checksum = msg["checksum"]
                    data_checksum = zlib.crc32(msg["data"].encode())
                    if checksum != data_checksum:
                        self.log("DATA WAS CORRUPTED %s" % seqnum)
                    else:

                        self.send_ack(msg, seqnum) # ack no matter if in order or not

                        # if in order, recursive print
                        if seqnum == self.seqn_to_print:
                            self.print_recursive(msg)
                except JSONDecodeError:
                    self.log("JSON PACKAGE CORRUPTED ON RECEIVER SIDE")
                    
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='receive data')
    args = parser.parse_args()
    sender = Receiver()
    sender.run()
