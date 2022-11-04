A simple transport protocol that provides reliable datagram service.
Transfers a file reliably between two nodes (a sender and a receiver).

Command line syntax:

```
$ ./3700send <recv_host> <recv_port>

$ ./3700recv
```

Our high-level approach:
1. Implement simple stop-and-wait with a window of 2 packets.
2. Add ```seqn```field to the packet in order to print packets in the order they were sent.
3. Expanded the window to send 4 packets before waiting for an ack.
4. Added ```check_timeouts()``` and ```retransmit``` logic for the detection and retransmission of dropped packets. Used a threshold of 2s.
5. Added ```checksum```field to the packet and logic in order to protect against corrupted message or ack packets.
6. Changed our timeout detection logic to retransmit based on a moving average of the round trip time (rtt) of packets. Initially, the rtt estimation is that of the very first sample (the first ack we get). Then, each subsequent ack, a weighted average using ```ALPHA``` is applied to adjust the moving average based on the new sample.
7. To accomodate varying bandwidths, we use a ```packet_dropped``` flag in order to perform congestion control. This flag allows us to probe the receiver for congestion and adjust our window accordingly.


Challenges:
- Often, adding a next feature (packet drop mitigation, congestion control, window expansion, use of rtt estimation, etc.) would cause previously functioning levels to fail. So, we frequently had to understand the various forces as play between simulations targeting different characteristics in order to understand what changed.
- Ultimately, testing gave different results on our local machine than on Gradescope. We found it difficult to debug issues which failed remotely but not on our machine. Our code passes all levels locally but not remotely.


Properties of design:
- a minimal but comprehensive set of data structures which allow us to maintain as much state as necessary to perform reliable transport
    - used dictionaries in order to have constant O(1) time access for frequent checks, ie checks for which packets are ```awaiting_ack``` on sender side or are ```acked``` on recv side.
- minimal additions to the fields of the data packet in order to minimize total bytes sent
- a ```print_recursive()``` function on recv side which automates printing of all in-order acked packets in constant time
- as discussed in high-level approach, use of probing for congestion control as well as round trip time estimation in order to more or less aggresively retransmit based on latency
  

Testing:
We tested via the command line, at each level inspecting the output, what drops or mangling were occuring, what round trip time averages were occuring, etc, in order to understand the problems our programs needed to respond to. Since timeouts may inherently behave different on different machines, at times we needed to run our program remotely in order to see how it is behaving for the Khoury machines, which was not necessarily the same as on our own machines.