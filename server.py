import json
import socket
import time
import signal
import sys
import struct
import concurrent.futures
import requests
import os
server_socket = None
LOCAL_ADDR=sys.argv[1]
LOCAL_PORT=int(sys.argv[2])
ALT_PORT=int(sys.argv[3])
ALT_PORT_ADVERTISED=sys.argv[4]
OTHER_ADDR=sys.argv[5]
def signal_handler(sig, frame):
    server_socket.close()
    sys.exit(0)

def start_server():
    signal.signal(signal.SIGINT, signal_handler)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((LOCAL_ADDR, LOCAL_PORT))
    server_socket.settimeout(1)
    server_socket.listen(1)
    print("listening...")
    client_socket = client_address = None
    client_socket2 = client_address2 = None
    while True:
        try:
            client_socket, client_address = server_socket.accept()
        except socket.timeout as e:
            continue
        client_ip, client_port = client_address
        client_socket.settimeout(5)
        print(f"from {client_ip}:{client_port}:")
        try:
            message = client_socket.recv(1024).decode('utf-8')
            print(f"received: {message}")
            rec = json.loads(message)
            nonce = str(rec["nonce"])
            wait=rec["wait"]+0
        except Exception as e:
            print("input error")
            print(e)
            client_socket.close()
            continue
        # the second socket
        socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # wait 2 secs (max) when closed
        socket2.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 2))
        socket2.bind((LOCAL_ADDR, ALT_PORT))
        socket2.settimeout(8)
        socket2.listen(1)
        # send back client information
        client_socket.send(("{"+f"""
        "you": "{client_ip}:{client_port}",
        "secondary port": {ALT_PORT_ADVERTISED}
        """+"}").encode('utf-8'))
        try:
            client_socket2, client_address2 = socket2.accept()
        except socket.timeout: #no connection from the client
            socket2.close()
            print("no connection received at the secondary port")
            continue
        client_socket2.settimeout(4)
        print(client_socket2.recv(1024).decode('utf-8'))
        client_ip2, client_port2 = client_address2
        # ACK with client information
        client_socket2.send(("{"+f"""
        "you": "{client_ip2}:{client_port2}"
        """+"}").encode('utf-8'))
        client_socket2.close()
        time.sleep(max(min(wait,1), 5))
        print("end waiting")
        socket2.close()
        def send_nonce(srcaddr, srcport, use_proxy):
            socket3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            socket3.settimeout(5)
            try:
                socket3.bind((srcaddr, srcport))
                if use_proxy and 'http_proxy' in os.environ:
                    _response = requests.get(f'http://{client_ip2}:{client_port}/{nonce}',proxies={"http":os.environ['http_proxy']},timeout=5)
                    print("done")
                else:
                    socket3.connect((client_ip2,client_port))
                    print("connected",socket3.getsockname())
                    socket3.send(nonce.encode('utf-8'))
                    socket3.close()
                    print("socket3 closed")
            except socket.timeout as e:
                print("timed out",socket3.getsockname())
                socket3.close()
                return
            except Exception as e:
                print("er"+srcaddr+":"+str(srcport))
                print(e)
                return
        with concurrent.futures.ThreadPoolExecutor() as executor:
            fn1 = executor.submit(send_nonce, LOCAL_ADDR, ALT_PORT, False)
            fn2 = executor.submit(send_nonce, LOCAL_ADDR, 0, False)
            fn3 = executor.submit(send_nonce, OTHER_ADDR, 0, True)
        fn1.result()
        fn2.result()
        fn3.result()
        client_socket.send(("done").encode('utf-8'))
        print("send")


if __name__ == "__main__":
    start_server()
