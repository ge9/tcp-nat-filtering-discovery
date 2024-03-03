# TCP NAT filtering discovery
This is a simple tool for NAT filtering discovery in TCP. This is NOT a STUN server/client, though inspired by it.
NAT behavior discovery in TCP is possible with [Stuntman](https://www.stunprotocol.org/) (note that you should specify the local port because of [this issue](https://github.com/jselbie/stunserver/issues/54#issuecomment-1963279852)). NAT discovery in UDP is possible with Stuntman, [coturn](https://github.com/coturn/coturn), etc.
# Mechanics
First, the client sends an initial message (nonce and waiting time) to the server's main port.
The server prepares the secondary port and send back information about it. Then, the client sends a packet to the secondary port.
After the given waiting time passed, the server sends test packets from three ports: the secondary port (same address and port), a random port on the main address (same address but different port), a random port on the alternative address (different address).
The client accepts the test packets for some time and shows the result.
# Usage
## server
`python server.py LOCAL_ADDR LOCAL_PORT LOCAL_PORT2 LOCAL_PORT2_ADVERTISED ALT_LOCAL_ADDR`
`LOCAL_ADDR` and `LOCAL_PORT` is the main address/port. `LOCAL_PORT2` is the secondary port, which is advertised as `LOCAL_PORT2_ADVERTISED` for the client. The `ALT_LOCAL_ADDR` is used as the outgoing port for the third test packet.

## client
`client.py SERVER_ADDR_OR_HOSTNAME SERVER_PORT LOCAL_ADDR LOCAL_PORT`
`LOCAL_ADDR` and `LOCAL_PORT` can be `""` and `0` respectively (automatically chosen).

# Interpretation of the result
```
A: same address and port
B: same address, different port
C: different address
```
1. A, B, C ... Endpoint Independent Filtering
2. A, B ... Address Dependent Filtering
3. A ... Address and Port Dependent Filtering
4. None ... Connection Dependent Filtering

Also, some system (router) may not receive packet from the exact port that internal device accessed (namely, A), resulting in only receiving B and C , or only B, or none.