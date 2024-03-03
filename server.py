import json
import socket
import time
import signal
import sys
import concurrent.futures
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
        print(f"from {client_ip}:{client_port}:")
        message = client_socket.recv(1024).decode('utf-8')
        print(f"received: {message}")
        try:
            rec = json.loads(message)
            nonce = str(rec["nonce"])
            wait=rec["wait"]+0
        except Exception:
            print("parse error")
            continue
        # the second socket
        socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        print(client_socket2.recv(1024).decode('utf-8'))
        client_ip2, client_port2 = client_address2
        # ACK with client information
        client_socket2.send(("{"+f"""
        "you": "{client_ip2}:{client_port2}"
        """+"}").encode('utf-8'))
        time.sleep(max(min(wait,0.5), 5))
        print("end waiting")
        client_socket2.shutdown(2)
        client_socket2.close()
        #socket2.shutdown(2)
        socket2.close()
        time.sleep(0.5)# wait for the port released
        fu1=fu2=fu3=None
        with concurrent.futures.ThreadPoolExecutor() as executor:
            fn1 = executor.submit(send_nonce, LOCAL_ADDR, ALT_PORT, client_ip2, client_port, nonce)
            fn2 = executor.submit(send_nonce, LOCAL_ADDR, 0, client_ip2, client_port, nonce)
            fn3 = executor.submit(send_nonce, OTHER_ADDR, 0, client_ip2, client_port, nonce)
        fn1.result()
        fn2.result()
        fn3.result()
        client_socket.send(("done").encode('utf-8'))
        print("send")

def send_nonce(srcaddr, srcport, destip, destport, nonce):
    socket3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket3.settimeout(5)
    try:
        socket3.bind((srcaddr, srcport))
        socket3.connect((destip,destport))
        print("connected",socket3.getsockname())
    except socket.timeout as e:
        print("timed out",socket3.getsockname())
        socket3.shutdown(2)
        socket3.close()
        return
    except Exception as e:
        print("er"+srcaddr+str(srcport))
        print(e)
        return
    socket3.send(nonce.encode('utf-8'))
    socket3.shutdown(2)
    socket3.close()
    print("socket3 closed")
if __name__ == "__main__":
    start_server()
