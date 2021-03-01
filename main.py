from socket import *
import sys

if len(sys.argv) <= 1:
	print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
	sys.exit(2)

# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)
# Fill in start.
serverName = sys.argv[1]
serverPort = 8080
tcpSerSock.bind((serverName, serverPort))
tcpSerSock.listen(1)
# Fill in end.

while 1:
	# Strat receiving data from the client
	print('Ready to serve...')
	tcpCliSock, addr = tcpSerSock.accept()
	print('Received a connection from:', addr)
	message = tcpCliSock.recv(1028).decode()
	print(message)
	# Extract the filename from the given message
	print(message.split()[1])
	messageSplit = message.split()
	messageParti = messageSplit[1].partition("/")
	filename = message.split()[1].partition("/")[2]
	if filename[0] == '/':
		filename = filename[1:]
	filename = ".".join(filename.split("/"))
	print(filename)
	fileExist = False
	filetouse = "/" + filename
	print(filetouse)
	try:
		# Check whether the file exist in the cache
		f = open(filetouse[1:], "r")
		outputdata = f.readlines()
		fileExist = True
		# ProxyServer finds a cache hit and generates a response message
		tcpCliSock.send("HTTP/1.0 200 OK\r\n")
		tcpCliSock.send("Content-Type:text/html\r\n")
		
		# TODO send outputdata to client socket
		# This may or may not be working. Havent tested it because I'm working on
		# the next part which does the actual storing of the data to the file stream.
		# Fill in start.
		for d in outputdata:
			sentCheck = tcpCliSock.sendall(d.encode())
			if sentCheck is not None:
				raise RuntimeError("socket connection broken")
		# Fill in end.
		
		print('Read from cache')
	# Error handling for file not found in cache
	except IOError:
		if not fileExist:
			# Create a socket on the proxyserver
			# TODO Fill in start.
			c = socket(AF_INET, SOCK_STREAM)
			# Fill in end.
			
			hostn = filename.replace("www.", "", 1)
			print(hostn)
			
			try:
				# TODO Connect the socket to port 80
				# Fill in start.
				c.connect((hostn, 80))
				# c.connect(hostn)
				# Fill in end.
				
				# Create a temporary file on this socket and ask port 80 for the file requested by the client
				fileobj = c.makefile('r', 0)
				fileobj.write("GET " + "http://" + filename + "HTTP / 1.0\n\n")
				
				# TODO Read the response into buffer
				# Fill in start.
				cmessage = c.recv(1028)
				c.close()
				# Fill in end.
				
				# TODO Create a new file in the cache for the requested file.
				# Also send the response in the buffer to client socket and the corresponding file in the cache
				# Fill in start.
				tmpFile = open("./" + filename, "wb")
				tmpFile.writelines(cmessage.splitlines())
				tcpCliSock.sendall(cmessage)
				# Fill in end.
			except:
				print("Illegal request")
		else:
			print("REMOVE THIS!!")
			# TODO HTTP response message for file not found
			# Fill in start.
			# Fill in end.
	
	# Close the client and the server sockets
	tcpCliSock.close()

# TODO
# Fill in start.
tcpSerSock.close()
# Fill in end.
