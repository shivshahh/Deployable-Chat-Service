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
        self.redis = self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            username=os.getenv("REDIS_USER", None),
            password=os.getenv("REDIS_PASSWORD", None),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
    
    def save_message(self, username, message):
        msg = f"[{username}]: {message}"
        self.redis.rpush("chat_history", msg)
                
    def send_history(self, connection):
        history = self.redis.lrange("chat_history", 0, -1)
        for entry in history:
            connection.sendall((entry + "\n").encode('utf-8'))
        connection.sendall("HISTORY_END\n".encode('utf-8'))

    # Sends out a message to all the connections
    def broadcast(self, username, message):

        if "HISTORY_END" in message:
            return
        
        message = message.rstrip("\n") 
        broadcast_msg = f"[{username}]: " + message 

        if username != "server":
            self.save_message(username, message)

        for connection in self.connections:
            if connection != username and self.connections[connection] is not None:
                self.connections[connection].sendall(broadcast_msg.encode('utf-8'))

    # Each users connection runs in this thread that waits for a message
    def user_thread(self, username):
        connection = self.connections[username]

        # Send message history first
        self.send_history(connection)

        # NOW broadcast to others that user joined
        self.broadcast("server", f"[{username}] connected")

        while True:
            msg = connection.recv(1024).decode('utf-8')

            if not msg:
                print(f"[{username}] disconnected")
                connection.close()
                self.connections[username] = None
                self.broadcast("server", f"[{username}] disconnected")
                break

            self.broadcast(username, msg)

    def execute(self, sock):
        try:
            sock.bind(('0.0.0.0', self.port))
            sock.listen()
            print("Listening for connections on: " + str(self.port))

            while True:
                # Accept a new connection
                client_connection, ip = sock.accept()
                client_username = client_connection.recv(1024).decode('utf-8').strip()

                # Track connection
                self.connections[client_username] = client_connection

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
