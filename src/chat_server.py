import sys
import socket
import threading
import redis
import os
import json

class ChatServer:
    def __init__(self, port):
        self.port = int(port)
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
    
    def save_message(self, username, recipient, message):
        msg_obj = {
            "sender": username,
            "recipient": recipient,
            "message": message
        }
        self.redis.rpush("chat_history", json.dumps(msg_obj))
                

    def send_history(self, connection, username, recipient):
        history = self.redis.lrange("chat_history", -1000, -1)
        
        try:
            for raw in history:
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                sender = entry["sender"]
                rec = entry["recipient"]
                msg = entry["message"]

                # Broadcast messages
                if recipient == "BROADCAST" and rec == "BROADCAST":
                    connection.sendall(
                        f"[{sender}]:[{rec}] {msg}\n".encode("utf-8")
                    )
                # Private 1:1 channel
                elif rec == recipient and sender == username:
                    connection.sendall(
                        f"[{sender}]:[{rec}] {msg}\n".encode("utf-8")
                    )
                elif rec == username and sender == recipient:
                    connection.sendall(
                        f"[{sender}]:[{rec}] {msg}\n".encode("utf-8")
                    )

            connection.sendall("HISTORY_END\n".encode("utf-8"))

        except (OSError, BrokenPipeError, ConnectionResetError):
            raise

    def push(self, username, recipient, message):

        if "HISTORY_END" in message:
            return
        
        message = message.rstrip("\n")
        push_msg = f"[{username}]: {message}"

        if username != "server":
            self.save_message(username, recipient, message)

        # Broadcast
        if recipient == "BROADCAST":
            with self.connections_lock:
                connection_keys = list(self.connections.keys())
            
            for connection_name in connection_keys:
                if connection_name != username:
                    with self.connections_lock:
                        conn_data = self.connections.get(connection_name)
                    
                    if conn_data is not None:
                        conn_socket = conn_data[0]
                        try:
                            conn_socket.sendall(
                                ("\\BROADCAST/" + push_msg + "\n").encode("utf-8")
                            )
                        except (OSError, BrokenPipeError, ConnectionResetError):
                            with self.connections_lock:
                                if connection_name in self.connections:
                                    del self.connections[connection_name]
                            pass
        else:
            
            with self.connections_lock:
                conn_data = self.connections.get(recipient)
            
            if conn_data is not None:
                conn_socket = conn_data[0]
                try:
                    conn_socket.sendall((push_msg + "\n").encode("utf-8"))
                except (OSError, BrokenPipeError, ConnectionResetError):
                    with self.connections_lock:
                        if recipient in self.connections:
                            del self.connections[recipient]
                    pass

    def user_thread(self, username):
        with self.connections_lock:
            conn_data = self.connections.get(username)
            if conn_data is None:
                return
            connection, recipient = conn_data
        
        try:
            self.send_history(connection, username, recipient)
        except:
            with self.connections_lock:
                if username in self.connections:
                    del self.connections[username]
            return

        self.push("server", recipient, f"[{username}] connected")

        while True:
            try:
                msg = connection.recv(1024).decode('utf-8')
            except:
                msg = None

            if not msg:
                print(f"[{username}] disconnected")
                try:
                    connection.close()
                except:
                    pass
                with self.connections_lock:
                    if username in self.connections:
                        del self.connections[username]
                self.push("server", recipient, f"[{username}] disconnected")
                break

            self.push(username, recipient, msg)

    def execute(self, sock):
        try:
            sock.bind(('0.0.0.0', self.port))
            sock.listen()
            print("Listening for connections on: " + str(self.port))

            while True:
                client_connection, ip = sock.accept()
                client_info = client_connection.recv(1024).decode('utf-8').strip()

                client_username = client_info.split('--')[0]
                client_recipient = client_info.split('--')[1]

                with self.connections_lock:
                    self.connections[client_username] = (client_connection, client_recipient)

                print(f"[{client_username}] connected")

                threading.Thread(
                    target=self.user_thread,
                    args=(client_username,)
                ).start()

        except OSError:
            print("Failed to bind to port: " + str(self.port))

    def __str__(self):
        return "Port: " + str(self.port)

def main():
    if(len(sys.argv) < 2):
        print("Usage: python3 chat_server.py [port]")
        return

    server = ChatServer(sys.argv[1])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("--- Server config ---\n" + str(server))
    server.execute(sock)

if __name__ == "__main__":
    main()
