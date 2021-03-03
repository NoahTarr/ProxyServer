import errno
from socket import *
import sys
import os, os.path


# Code adapted from example here: https://www.geeksforgeeks.org/creating-a-proxy-webserver-in-python-set-1/
def getURLAndFile(request):
	# parse the first line
	first_line = request.split('\n')[0]
	# get url
	url = first_line.split(' ')[1]
	# remove leading /
	while url[0] == '/':
		url = url[1:]
	
	# get destination address and port (if it exists)
	http_pos = url.find("://")  # find pos of ://
	if http_pos == -1:
		temp = url
	else:
		temp = url[(http_pos + 3):]  # get the rest of url
	
	port_pos = temp.find(":")  # find the port pos (if any)
	
	# find end of web server
	webserver_pos = temp.find("/")
	if webserver_pos == -1:
		webserver_pos = len(temp)
	
	filename = ""
	webserver = ""
	port = -1
	if port_pos == -1 or webserver_pos < port_pos:
		# default port
		filename = temp
		webserver = temp[:webserver_pos]
		port = 80
	else:  # specific port
		port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
		webserver = temp[:port_pos]
		filename = webserver + temp[port_pos + len(str(port)):]
	
	return filename, webserver, port


serverName = ""
if len(sys.argv) <= 1:
	print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
	sys.exit(2)
elif sys.argv[1] == "host":
	serverName = gethostname()
else:
	serverName = sys.argv[1]

# Create a server socket, bind it to a port and start listening
serverPort = 8080
tcpSerSock = socket(AF_INET, SOCK_STREAM)
# Fill in start.
tcpSerSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
tcpSerSock.bind((serverName, serverPort))
tcpSerSock.listen(1)

# Fill in end.


while 1:
	# Strat receiving data from the client
	print('Ready to serve...')
	tcpCliSock, addr = tcpSerSock.accept()
	print('Received a connection from:', addr)
	message = tcpCliSock.recv(1028)
	cliRequest = message
	message = message.decode()
	print(message)
	# Extract the filename from the given message
	filename, hostn, portn = getURLAndFile(message)
	print(filename)
	print(hostn)
	print(portn)
	fileExist = False
	filePath = os.getcwd() + "/cached/" + filename
	print(filePath)
	
	try:
		# Check whether the file exist in the cache
		f = open(filePath, "rb")
		outputdata = f.readlines()
		fileExist = True
		# ProxyServer finds a cache hit and generates a response message
		tcpCliSock.send("HTTP/1.0 200 OK\r\n".encode())
		tcpCliSock.send("Content-Type:text/html\r\n".encode())
		
		# TODO send outputdata to client socket
		# This may or may not be working. Havent tested it because I'm working on
		# the next part which does the actual storing of the data to the file stream.
		# Fill in start.
		for d in outputdata:
			sentCheck = tcpCliSock.sendall(d)
			if sentCheck is not None:
				raise RuntimeError("socket connection broken")
		# Fill in end.
		
		print('Read from cache')
	# Error handling for file not found in cache
	except (IOError, FileNotFoundError):
		if not fileExist:
			# Create directory for file if it doesnt exist
			try:
				os.makedirs(os.path.dirname(filePath))
			except OSError as exc:  # Python >2.5
				if exc.errno == errno.EEXIST and os.path.isdir(os.path.dirname(filePath)):
					pass
				else:
					raise
			
			# TODO Create a socket on the proxyserver
			# Fill in start.
			c = socket(AF_INET, SOCK_STREAM)
			# Fill in end.
			
			try:
				# TODO Connect the socket to port 80
				# Fill in start.
				c.connect((hostn, portn))
				# c.send(message.encode())
				# Fill in end.
				
				# Create a temporary file on this socket and ask port 80 for the file requested by the client
				# fileobj = c.makefile('r', 0)
				# filePath = os.getcwd() + filetouse
				# try:
				# 	os.makedirs(os.path.dirname(filePath))
				# except OSError as exc:  # Python >2.5
				# 	if exc.errno == errno.EEXIST and os.path.isdir(os.path.dirname(filePath)):
				# 		pass
				# 	else:
				# 		raise
				
				# fileobj = open(filePath, "w")
				# fileobj.flush()
				# fileobj.write("GET " + "http://" + filename + "HTTP / 1.0\n\n")
				# fileobj.close()
				# fileobj = open(filePath, "r")
				# c.sendall(fileobj.read().encode())
				# c.send(cliRequest)
				getReq = "GET " + filename.replace(hostn, "") + " HTTP/1.1\r\n"
				getReq += "Host: " + hostn + "\r\n"
				getReq += "Connection: close\r\n\r\n"
				c.send(getReq.encode())
				# c.send(("GET " + filename + "HTTP/1.0\n\n").encode())
				
				# TODO Read the response into buffer
				# Fill in start.
				cmessage = []
				# Continue to receive data until 0 received
				while 1:
					data = c.recv(1028)
					
					if len(data) > 0:
						cmessage.append(data)
					else:
						c.close()
						break
				# Fill in end.
				
				# TODO Create a new file in the cache for the requested file.
				# Also send the response in the buffer to client socket and the corresponding file in the cache
				# Fill in start.
				fileobj = open(filePath, "wb")
				fileobj.flush()
				fileobj.writelines(cmessage)
				for m in cmessage:
					sentCheck = tcpCliSock.sendall(m)
					if sentCheck is not None:
						raise RuntimeError("socket connection broken")
				fileobj.close()
			# Fill in end.
			except ValueError:
				print(ValueError)
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
