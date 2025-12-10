import sys
import socket
import threading
import redis
import os

class ChatServer:
    def __init__(self, port):
        self.port = int(port)
        # Dictionary that maps username to connection socket
        self.connections = {}
        self.connections_lock = threading.Lock()
        self.redis = self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            username=os.getenv("REDIS_USER", None),
            password=os.getenv("REDIS_PASSWORD", None),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
    
    def save_message(self, username, recipient, message):
        msg = f"[{username}]:[{recipient}] {message}"
        self.redis.rpush("chat_history", msg)
                
    def send_history(self, connection, username, recipient):
        # Limit history to last 1000 messages to prevent memory issues
        history = self.redis.lrange("chat_history", -1000, -1)
        
        try:
            for entry in history:
                tag = entry.split()[0]

                if recipient == "BROADCAST" and "BROADCAST" in tag:
                    connection.sendall((entry + "\n").encode('utf-8'))
                elif tag == "[" + username + "]:[" + recipient + "]" or tag == "[" + recipient + "]:[" + username + "]":    
                    connection.sendall((entry + "\n").encode('utf-8'))

            connection.sendall("HISTORY_END\n".encode('utf-8'))
        except (OSError, BrokenPipeError, ConnectionResetError):
            # Connection closed during history send, let caller handle it
            raise

    # Pushes out messages to the appropriate connections
    def push(self, username, recipient, message):

        if "HISTORY_END" in message:
            return
        
        message = message.rstrip("\n") 
        push_msg = f"[{username}]: " + message 

        if username != "server":
            self.save_message(username, recipient, message)

        if recipient == "BROADCAST":
            # Create a copy of connection keys to avoid modification during iteration
            with self.connections_lock:
                connection_keys = list(self.connections.keys())
            
            for connection_name in connection_keys:
                if connection_name != username:
                    with self.connections_lock:
                        conn_data = self.connections.get(connection_name)
                    
                    if conn_data is not None:
                        conn_socket = conn_data[0]
                        try:
                            conn_socket.sendall(("\\BROADCAST/" + push_msg + "\n").encode('utf-8'))
                        except (OSError, BrokenPipeError, ConnectionResetError):
                            # Connection is closed, clean it up
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
                    conn_socket.sendall((push_msg + "\n").encode('utf-8'))
                except (OSError, BrokenPipeError, ConnectionResetError):
                    # Connection is closed, clean it up
                    with self.connections_lock:
                        if recipient in self.connections:
                            del self.connections[recipient]
                    pass

    # Each users connection runs in this thread that waits for a message
    def user_thread(self, username):
        with self.connections_lock:
            conn_data = self.connections.get(username)
            if conn_data is None:
                return
            connection, recipient = conn_data
        
        # TODO modify so only recipient history is sent
        # Send message history first
        try:
            self.send_history(connection, username, recipient)
        except (OSError, BrokenPipeError, ConnectionResetError):
            # Connection closed before history could be sent
            with self.connections_lock:
                if username in self.connections:
                    del self.connections[username]
            return

        # Send that user joined
        self.push("server", recipient, f"[{username}] connected")

        while True:
            try:
                msg = connection.recv(1024).decode('utf-8')
            except (OSError, BrokenPipeError, ConnectionResetError):
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
                # Accept a new connection
                client_connection, ip = sock.accept()
                client_info = client_connection.recv(1024).decode('utf-8').strip()

                client_username = client_info.split('--')[0]
                client_recipient = client_info.split('--')[1]

                # Track connection
                with self.connections_lock:
                    self.connections[client_username] = (client_connection, client_recipient)

                print(f"[{client_username}] connected")

                # Start the user thread (will send history AND then broadcast join)
                connection_thread = threading.Thread(
                    target=self.user_thread,
                    args=(client_username,)
                )
                connection_thread.start()

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

    # Show server config
    print("--- Server config ---\n" + str(server))
    server.execute(sock)

if __name__ == "__main__":
    main()
