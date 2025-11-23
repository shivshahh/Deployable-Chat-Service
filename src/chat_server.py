import sys
import socket
import threading

class ChatServer:
	def __init__(self, port):
		self.port = int(port)
		# Dictionary that maps username to connection socket
		self.connections = {}
	
	# Sends out a message to all the connections
	def broadcast(self, username, message):
		broadcast_msg = "[" + username + "]: " + message 
		for connection in self.connections:
			if connection != username and self.connections[connection] is not None:
				self.connections[connection].sendall(broadcast_msg.encode('utf-8'))

	# Each users connection runs in this thread that waits for a message
	def user_thread(self, username):
		connection = self.connections[username]
		# TODO List users on join?
		# TODO Pull message history and send to user
		connection.sendall("HISTORY_END".encode('utf-8'))

		# Wait for input, send data when input recieved
		while True:
			msg = (connection.recv(1024)).decode('utf-8')

			# Client gracefully closes connection
			if not msg:
				print("[" + username + "] disconnected")
				connection.close()
				self.connections[username] = None
				self.broadcast("server", "[" + username + "] disconnected\n")
				break

			self.broadcast(username, msg)

	def execute(self, sock):
		try:
			sock.bind(('127.0.0.1', self.port))
			sock.listen()
			print("Listening for connections on: " + str(self.port))

			while True:
				# When a connection happens get the username and send to thread
				client_connection, ip = sock.accept()
				client_username = (client_connection.recv(1024)).decode('utf-8')

				connection_thread = threading.Thread(target=self.user_thread, args=(client_username,))
				
				# Track the thread for each user
				self.connections[client_username] = client_connection

				print("[" + client_username + "] connected")
				self.broadcast("server", "[" + client_username + "] connected\n")
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
