# TCP NAT filtering discovery
This is a simple NAT filtering discovery tool for TCP. This is NOT a STUN server/client, though inspired by it. See [RFC 5382](https://datatracker.ietf.org/doc/html/rfc5382) for concepts in TCP NAT.

NAT mapping discovery in TCP is possible with [Stuntman](https://www.stunprotocol.org/) (note that you should specify the local port because of [this issue](https://github.com/jselbie/stunserver/issues/54#issuecomment-1963279852)). NAT discovery in UDP is possible with Stuntman, [coturn](https://github.com/coturn/coturn), etc.

# Mechanics
First, the client sends an initial message (nonce and waiting time) to the server's main port.

The server prepares the secondary port and returns it with additional information of client IP/Port. 

Then, the client sends a packet to the secondary port. The server again returns client IP/Port, which is used for NAT mapping discovery.

After the given waiting time passed, the server sends test packets from three ports: the secondary port (same address and port), a random port on the main address (same address but different port), a random port on the alternative address (different address).

The client accepts the test packets for some time and shows the result.
# Usage
## server
`python server.py LOCAL_ADDR LOCAL_PORT LOCAL_PORT2 LOCAL_PORT2_ADVERTISED ALT_LOCAL_ADDR`

`LOCAL_ADDR` and `LOCAL_PORT` is the main address/port. `LOCAL_PORT2` is the secondary port, which is advertised as `LOCAL_PORT2_ADVERTISED` for the client. The `ALT_LOCAL_ADDR` is used as the outgoing port for the third test packet. If environment variable `http_proxy` is set, the third test packet will be sent through the proxy.

## client
`python client.py SERVER_ADDR_OR_HOSTNAME SERVER_PORT LOCAL_ADDR LOCAL_PORT`

`LOCAL_ADDR` and `LOCAL_PORT` can be `""` and `0` respectively (automatically chosen).

## Accepting connection from the same IP/Port

In testing, the client connects to the secondary port and both sides gracefully close the connection, so the client TCP port goes into TIME_WAIT state.

Then, client waits for inbound connections. Accepting a connection from the secondary port (the exact port the client connected just before) can be prohibited by the previous TIME_WAIT.

Linux (including Android) seems to allow "overriding" the TIME_WAIT by the inbound connection, but Windows (and probably macOS judging from my incomplete testing) and some routers doesn't. 

Note: Linux seems not to allow overriding the CLOSE status of TCP.

This tool lastly prints a line beginning with `Can accept connection from the same IP/Port: ` indicating whether the client could accept connection from the secondary port.

It seems that whether inbound connection in TIME_WAIT can be overrided by outbound connection and whether outbound connection in TIME_WAIT can be overrided by inbound connection are equivalent.

Therefore, if the client in a machine could not accept connection from the same IP/Port, the machine will be inappropriate as the server side of this tool.