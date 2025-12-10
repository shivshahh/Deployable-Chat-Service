import sys
import socket
import threading
import redis
import os
import json


class ChatServer:
    def __init__(self, port):
        self.port = int(port)
        
        # username → (socket, recipient)
        self.connections = {}
        self.connections_lock = threading.Lock()

        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            username=os.getenv("REDIS_USER", None),
            password=os.getenv("REDIS_PASSWORD", None),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )

    # ------------------------------
    # STORE MESSAGES IN STRUCTURED JSON
    # ------------------------------
    def save_message(self, sender, recipient, message):
        data = {
            "sender": sender,
            "recipient": recipient,
            "message": message
        }
        self.redis.rpush("chat_history", json.dumps(data))

    # ------------------------------
    # SEND HISTORY SAFELY
    # ------------------------------
    def send_history(self, conn, username, recipient):
        history = self.redis.lrange("chat_history", -1000, -1)

        for entry_str in history:
            entry = json.loads(entry_str)

            sender = entry["sender"]
            recv = entry["recipient"]

            # Broadcast history
            if recipient == "BROADCAST":
                if recv == "BROADCAST":
                    conn.sendall(f"[{sender}]: {entry['message']}\n".encode("utf-8"))
                continue

            # Private chat history (sender <-> recipient only)
            if (sender == username and recv == recipient) or \
               (sender == recipient and recv == username):

                conn.sendall(f"[{sender} → {recv}]: {entry['message']}\n".encode("utf-8"))

        conn.sendall("HISTORY_END\n".encode("utf-8"))

    # ------------------------------
    # SEND MESSAGE TO TARGET
    # ------------------------------
    def push(self, sender, recipient, message):

        if sender != "server":
            self.save_message(sender, recipient, message)

        # ---------- BROADCAST ----------
        if recipient == "BROADCAST":
            msg = f"[{sender}]: {message}\n"

            with self.connections_lock:
                for user, (sock, _) in list(self.connections.items()):
                    if user != sender:
                        try:
                            sock.sendall(msg.encode("utf-8"))
                        except:
                            del self.connections[user]

            return

        # ---------- PRIVATE ----------
        with self.connections_lock:
            target = self.connections.get(recipient)

        if target:
            sock, _ = target
            try:
                sock.sendall(f"[{sender} → {recipient}]: {message}\n".encode("utf-8"))
            except:
                with self.connections_lock:
                    if recipient in self.connections:
                        del self.connections[recipient]

    # ------------------------------
    # PER-USER THREAD
    # ------------------------------
    def user_thread(self, username):
        with self.connections_lock:
            conn, recipient = self.connections[username]

        try:
            self.send_history(conn, username, recipient)
        except:
            with self.connections_lock:
                del self.connections[username]
            return

        # Notify others
        self.push("server", recipient, f"{username} joined")

        while True:
            try:
                msg = conn.recv(4096).decode("utf-8")
            except:
                msg = None

            if not msg:
                print(f"[{username}] disconnected")
                try:
                    conn.close()
                except:
                    pass

                with self.connections_lock:
                    if username in self.connections:
                        del self.connections[username]

                self.push("server", recipient, f"{username} disconnected")
                break

            self.push(username, recipient, msg.strip())

    # ------------------------------
    # SERVER LISTENER
    # ------------------------------
    def execute(self, sock):
        try:
            sock.bind(("0.0.0.0", self.port))
            sock.listen()
            print("Listening on port", self.port)

            while True:
                conn, addr = sock.accept()
                client_info = conn.recv(4096).decode("utf-8").strip()

                username, recipient = client_info.split("--")

                with self.connections_lock:
                    self.connections[username] = (conn, recipient)

                print(f"[{username}] connected")

                threading.Thread(target=self.user_thread, args=(username,), daemon=True).start()

        except OSError:
            print("Failed to bind to port", self.port)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 chat_server.py <port>")
        return

    server = ChatServer(sys.argv[1])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("--- Server config ---")
    print(server)

    server.execute(sock)


if __name__ == "__main__":
    main()
