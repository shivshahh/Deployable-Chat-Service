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

		while not user_break.is_set():
			try:
				msg = sock.recv(4096).decode('utf-8')
				if not msg:
					user_break.set()
					break

				# Clear current input line
				sys.stdout.write("\r")  
				sys.stdout.flush()

				# Print the server/broadcast message
				print(msg, end='')

				# Redraw prompt
				sys.stdout.write(f"\n[{self.username}]: ")
				sys.stdout.flush()

			except:
				user_break.set()
				break
	
	# Accepting user input to send to the server
	def writing_thread(self, sock, user_break):
		while True:
			user_input = input(f"[{self.username}]: ")

			if user_input == "exit":
				user_break.set()
				try:
					sock.shutdown(socket.SHUT_RDWR)  # unblock reader thread
				except:
					pass
				break

			sock.sendall(user_input.encode('utf-8'))

	
	def execute(self, sock):
		try:
			sock.connect((self.host, self.port))
			print("Connected to the chat server")

			# Send username
			sock.sendall(self.username.encode('utf-8'))

			# Get message history
			buffer = ""
			while True:
				chunk = sock.recv(4096).decode('utf-8')
				
				if not chunk:
					print("Server closed during history load.")
					return

				buffer += chunk

				# If HISTORY_END appears, stop reading history
				if "HISTORY_END" in buffer:
					history, remainder = buffer.split("HISTORY_END", 1)

					# Print all history messages
					if history.strip():
						print(history, end='')
					buffer = ""
					break

			# Will join when user is done
			user_break = threading.Event()

			# Reads responses from server
			server_reader = threading.Thread(target=self.reading_thread, args=(sock, user_break))

			# Writes user input to server
			console_writer  = threading.Thread(target=self.writing_thread, args=(sock, user_break))

			server_reader.start()
			console_writer.start()

			# Joins after user_break is set
			server_reader.join()
			console_writer.join()

			sock.close()

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
