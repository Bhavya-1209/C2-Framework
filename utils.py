import json

def reliable_send(sock, data):
    json_data = json.dumps(data)
    sock.send(json_data.encode())

def reliable_recv(sock):
    data = ""
    while True:
        try:
            data += sock.recv(1024).decode()
            return json.loads(data)
        except ValueError:
            continue
