import json
import socket
import random
import time
import sys
import struct
import concurrent.futures
SERVER_ADDR = socket.gethostbyname(sys.argv[1])
SERVER_PORT = int(sys.argv[2])
CLIENT_ADDR = sys.argv[3]# "" is ok
CLIENT_PORT = int(sys.argv[4])# 0 is ok
def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.settimeout(10)
    client_socket.bind((CLIENT_ADDR, CLIENT_PORT))
    client_socket.connect((SERVER_ADDR, SERVER_PORT))
    myaddr, myport = client_socket.getsockname()

    # client's waiting time (in seconds)
    timeout = 1
    # additional waiting time for server
    LATENCY = 1
    nonce = str(random.randint(0, 65535))
    print(f"- (Phase 1) Connected from {myaddr}:{myport} to {SERVER_ADDR}:{SERVER_PORT}")
    message = "{"+f"""
    "nonce": {nonce},
    "wait": {timeout+LATENCY}
    """+"}"
    client_socket.send(message.encode('utf-8'))
    response = json.loads(client_socket.recv(1024))
    secondary_port = response["secondary port"]
    myport1 = response["you"]
    print(f"  - My external ip/port is {myport1}")
    client_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #intensionally send RST?
    #client_socket2.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
    client_socket2.settimeout(5)
    client_socket2.bind((myaddr, myport))
    client_socket2.connect((SERVER_ADDR, secondary_port))
    client_socket2.send(message.encode('utf-8'))
    print(f"- (Phase 2) Connected from {myaddr}:{myport} to {SERVER_ADDR}:{secondary_port}")
    response2 = json.loads(client_socket2.recv(1024))
    client_socket2.close()
    myport2 = response2["you"]
    print(f"  - My external ip/port is {myport2}")
    # Endpoint Independent seems more popular than Address Dependent
    print(f"Detected NAT mapping: {"Endpoint Independent (or Address Dependent)" if myport1 == myport2 else "Address and Port Dependent (or Connection Dependent)"}")
    time.sleep(timeout)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((CLIENT_ADDR, myport))
    server_socket.settimeout(10)
    server_socket.listen(1)
    print("- Awaiting response...")
    counter=0
    natFil=0#Connection Dependent
    canGetFromSamePort=False
    def process_packet(client_socket3,client_address3):
        nonlocal natFil, canGetFromSamePort
        client_ip3, client_port3 = client_address3
        resp1 = client_socket3.recv(1024).decode('utf-8')
        client_socket3.close()
        if resp1!=nonce and not resp1.startswith("GET /"+nonce):
            return            
        addrtype = None
        if client_ip3 == SERVER_ADDR:
            if client_port3 == secondary_port:
                addrtype="same address and port"; natFil=max(natFil, 1); canGetFromSamePort=True
            else:
                addrtype="same address, different port"; natFil=max(natFil, 2)
        else:
            addrtype="different address"; natFil=max(natFil, 3)
        print(f"- Got response from {client_ip3}:{client_port3} ({addrtype})")
    tasklist = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            try:
                client_socket3, client_address3 = server_socket.accept()    
                counter+=1
                if counter==5:# this may not happen
                    return
                tasklist.append(executor.submit(process_packet, client_socket3, client_address3))
            except socket.timeout:
                for task in tasklist:
                    task.result()
                try:
                    res=client_socket.recv(1024).decode('utf-8')
                    if (res == "done:"+nonce):
                        print("- All tests finished.")
                        print("Detected NAT filtering: " + ("Endpoint Independent" if natFil==3 else "Connection Dependent (or Address and Port Dependent)" if natFil==0 else f"{"Address and Port" if natFil==1 else "Address"} Dependent"))
                        print(f"Can accept connection from the same IP/Port: {"Yes" if canGetFromSamePort else "No"}")
                    else:
                        print("Error: unexpected last message from server")
                except socket.timeout:
                    print("Error: no last message from server. Server may be down.")
                client_socket.close()
                break
        
if __name__ == "__main__":
    start_client()
