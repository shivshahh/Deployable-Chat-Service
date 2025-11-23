import sys
import socket
import threading

# Class that houses all the chat client functinonality
class ChatClient:
	def __init__(self, host, port, username):
		self.host = host
		self.port = int(port)
		self.username = username

	# Reading what the server sends and printing out to console
	def reading_thread(self, sock, user_break):

		# If the user hasn't gracefully ended then keeping reading and outputting server content
		while not user_break.is_set():
			server_contents = sock.recv(4096).decode('utf-8')
			print(server_contents)
	
	# Accepting user input to send to the server
	def writing_thread(self, sock, user_break):
		while True:
			user_input = input("[" + self.username + "]")

			# Graceful shutdown of client
			if user_input == "exit":
				user_break.set()

			# Sending user message to the server
			sock.sendall(user_input.encode('utf-8'))

			if user_break.is_set():
				break
	
	def execute(self, sock):
		try:
			sock.connect((self.host, self.port))
			print("Connected to the chat server")

			# Send username
			sock.sendall(self.username.encode('utf-8'))

			# Get message history
			while True:
				msg_history = sock.recv(4096).decode('utf-8')
				
				if "HISTORY_END" == msg_history:
					break

				print(msg_history, end='')

			# Will join when user is done
			user_break = threading.Event()

			# Reads responses from server
			server_reader = threading.Thread(target=self.reading_thread, args=(sock, user_break))

			# Writes user input to server
			console_writer  = threading.Thread(targe=self.writer_thread, args=(sock, user_break))

			server_reader.start()
			console_writer.start()

			# Joins after user_break is set
			server_reader.join()
			console_writer.join()

		except ConnectionRefusedError:
			print("Could not connect to server")
			return

	def __str__(self):
		return "IP: " + self.host + "\nPort: " + str(self.port) + "\nUsername: " + self.username

def main():
	if(len(sys.argv) < 4):
		print("Usage: python3 chat_client.py [chat server ip] [chat server port] [username]")
		return
	
	client = ChatClient(sys.argv[1], sys.argv[2], sys.argv[3])
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Show user client options
	print("Type 'exit' to gracefully end client.\n--- Client config ---\n" + str(client))
	client.execute(sock)

if __name__ == "__main__":
	main()
