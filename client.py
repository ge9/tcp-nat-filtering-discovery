import json
import socket
import random
import time
import sys
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
    peeraddr, peerport = client_socket.getpeername()

    # client's waiting time (in seconds)
    timeout = 1
    # additional waiting time for server
    LATENCY = 1
    nonce = str(random.randint(0, 65535))
    print(f"connecting from {myaddr}:{myport} to {peeraddr}:{peerport}")
    print("nonce="+str(nonce))
    message = "{"+f"""
    "nonce": {nonce},
    "wait": {timeout+LATENCY}
    """+"}"
    client_socket.send(message.encode('utf-8'))
    response = json.loads(client_socket.recv(1024))
    print(response)
    secondary_port = response["secondary port"]
    client_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket2.settimeout(5)
    client_socket2.bind((CLIENT_ADDR, myport))
    client_socket2.connect((SERVER_ADDR, secondary_port))
    client_socket2.send("ok".encode('utf-8'))
    response2 = json.loads(client_socket2.recv(1024))
    client_socket2.shutdown(2)
    client_socket2.close()
    print("from the secondary port:", response2)

    time.sleep(timeout)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((CLIENT_ADDR, myport))
    server_socket.settimeout(10)
    server_socket.listen(1)
    print("awaiting response...")
    counter=0
    def process_packet(client_socket3,client_address3):
        client_ip3, client_port3 = client_address3
        resp1 = client_socket3.recv(1024).decode('utf-8')
        if resp1!=nonce:
            return
        addrtype = None
        if client_ip3 == SERVER_ADDR:
            if client_port3 == secondary_port:
                addrtype="same address and port"
            else:
                addrtype="same address, different port"
        else:
            addrtype="different address"
        print(f"got response from {client_ip3}:{client_port3} ({addrtype})")
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
                print("finished")
                print("message from server:"+client_socket.recv(1024).decode('utf-8'))
                client_socket.close()
                break
        
if __name__ == "__main__":
    start_client()
