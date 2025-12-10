import sys
import socket
import threading


class ChatClient:
    def __init__(self, host, port, username):
        self.host = host
        self.port = int(port)
        self.username = username
        self.recipient = None

    def reading_thread(self, sock, stop_event):

        while not stop_event.is_set():
            try:
                msg = sock.recv(4096).decode("utf-8")
                if not msg:
                    stop_event.set()
                    break

                sys.stdout.write("\r" + msg)
                sys.stdout.write(f"[{self.username}]: ")
                sys.stdout.flush()

            except:
                stop_event.set()
                break

    def writing_thread(self, sock, stop_event):

        while not stop_event.is_set():
            user_input = input(f"[{self.username}]: ")

            if user_input.lower() == "exit":
                stop_event.set()
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                break

            sock.sendall(user_input.encode("utf-8"))

    def execute(self, sock):

        try:
            sock.connect((self.host, self.port))
            print("Connected to server.\n")

            sock.sendall(f"{self.username}--{self.recipient}".encode("utf-8"))

            # -------- RECEIVE HISTORY FIRST --------
            buffer = ""
            while True:
                chunk = sock.recv(4096).decode("utf-8")
                buffer += chunk
                if "HISTORY_END" in buffer:
                    history, _ = buffer.split("HISTORY_END", 1)
                    if history.strip():
                        print(history)
                    break

            stop_event = threading.Event()
            threading.Thread(target=self.reading_thread, args=(sock, stop_event), daemon=True).start()
            threading.Thread(target=self.writing_thread, args=(sock, stop_event), daemon=True).start()

            while not stop_event.is_set():
                stop_event.wait(1)

            sock.close()

        except ConnectionRefusedError:
            print("Could not connect to server.")

    def __str__(self):
        return f"IP: {self.host}\nPort: {self.port}\nUsername: {self.username}\nRecipient: {self.recipient}"


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 chat_client.py <server_ip> <port> <username> [recipient]")
        return

    client = ChatClient(sys.argv[1], sys.argv[2], sys.argv[3])

    if len(sys.argv) == 5:
        client.recipient = sys.argv[4]
    else:
        client.recipient = "BROADCAST"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("Type 'exit' to quit.\n")
    print("--- Client config ---")
    print(client)

    client.execute(sock)


if __name__ == "__main__":
    main()
