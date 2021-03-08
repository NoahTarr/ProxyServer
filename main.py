import errno
from socket import *
from datetime import datetime
from sys import exit
import sys
import os.path
import shutil
import json

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
	
	while filename[len(filename) - 1] == '/':
		filename = filename[:len(filename) - 1]
	
	return url, filename, webserver, port


# def proxyProgram(times, serverName, serverPort):
if __name__ == '__main__':
	# for time comparison between cached and nonCached load times
	# dict: , value={"nonCached": (int), "cached": (int)}
	times = dict()
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
	tcpSerSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	tcpSerSock.settimeout(1.0)
	
	# Fill in start.
	# tcpSerSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	tcpSerSock.bind((serverName, serverPort))
	tcpSerSock.listen(1)
	# Fill in end.
	
	# Debugging
	if os.path.isdir(os.getcwd() + "/cached"):
		deleteCachedDirectory = ""
		while deleteCachedDirectory != 'y' and deleteCachedDirectory != 'n':
			deleteCachedDirectory = input("A directory of cached websites already exists. Do you want to delete it y/n: ")
		if deleteCachedDirectory == 'y':
			shutil.rmtree(os.getcwd() + "/cached")
	
	try:
		while True:
			# Start receiving data from the client
			print('Ready to serve...')
			time = 0
			message = 0
			tcpCliSock, addr = None, None
			while True:
				try:
					tcpCliSock, addr = tcpSerSock.accept()
					print('Received a connection from:', addr)
					time = datetime.today().timestamp()
					message = tcpCliSock.recv(2048)
					break
				except timeout:
					continue
			messageDecoded = message.decode()
			
			# Ignore connection attempts from google or spotify
			if len(message) == 0 or messageDecoded.find('google') != -1 or messageDecoded.find('spotify') != -1 or messageDecoded.find('127.0.0.1') != -1:
				tcpCliSock.shutdown(1)
				tcpCliSock.close()
				continue
			
			message = message.decode()
			print(message)
			# Extract the filename from the given message
			url, filename, hostn, _ = getURLAndFile(message)
			# I was obtaining portn from the incoming url, but it failed more often then just using port 80.
			portn = 80
			print("url: " + url)
			print("filename: " + filename)
			print("host: " + hostn)
			print("port: " + str(portn))
			
			fileExist = False
			filePath = os.getcwd() + "/cached/" + filename
			print("local file path: " + filePath)
			
			try:
				# Check whether the file exist in the cache
				f = open(filePath, "rb")
				outputdata = f.readlines()
				if len(outputdata) == 0:
					# Remove the file because it is empty
					os.remove(filePath)
					raise FileNotFoundError("File is empty in cache")
				fileExist = True
				# This is no longer needed b/c I stored the original response in the file with the website data
				# ProxyServer finds a cache hit and generates a response message
				# tcpCliSock.send("HTTP/1.1 200 OK\r\n".encode())
				# tcpCliSock.send("Content-Type:text/html\r\n".encode())
				
				# Send outputdata to client socket
				for i in range(len(outputdata)):
					sentCheck = tcpCliSock.sendall(outputdata[i])
					if sentCheck is not None:
						raise RuntimeError("socket connection broken")
				
				if filename not in times.keys():
					times[filename] = {
						"nonCached": -1,
						"cached": datetime.today().timestamp() - time
					}
				else:
					times[filename]["cached"] = datetime.today().timestamp() - time
				print('Read from cache')
				
			# Error handling for file not found in cache
			except (IOError, FileNotFoundError, RuntimeError):
				if not fileExist:
					# Create directory for file if it doesnt exist
					try:
						os.makedirs(os.path.dirname(filePath))
					except OSError as exc:  # Python >2.5
						# Directory already exists so continue
						if exc.errno == errno.EEXIST and os.path.isdir(os.path.dirname(filePath)):
							pass
						# A file exists with the same name as the directory. Delete the file to resolve
						elif exc.errno == errno.EEXIST and os.path.isfile(os.path.dirname(filePath)):
							os.remove(filePath)
							pass
						#Unknown error
						else:
							raise
						
						
					# Create a socket on the proxyserver
					c = socket(AF_INET, SOCK_STREAM)
					
					try:
						# Connect the socket to port 80
						c.connect((hostn, portn))
						getReq = "GET " + filename.replace(hostn, "") + " HTTP/1.1\r\n"
						if url[len(url) - 1] == '/':
							getReq = "GET " + filename.replace(hostn, "") + "/ HTTP/1.1\r\n"
						getReq += "Host: " + hostn + "\r\n"
						getReq += "Connection: Close\r\n\r\n"
						c.settimeout(60)
						c.sendall(getReq.encode())
						
						# Read the response into buffer
						cmessage = []
						# Continue to receive data until 0 received
						while 1:
							data = c.recv(2048)
							
							if data.find(b"404 Not Found") >= 0:
								raise RuntimeError("socket connection broken, 404 Not Found")
							elif len(data) > 0:
								cmessage.append(data)
							else:
								c.close()
								break
						
						# Create a new file in the cache for the requested file.
						# Also send the response in the buffer to client socket and the corresponding file in the cache
						if len(cmessage) > 0:
							for m in cmessage:
								sentCheck = tcpCliSock.sendall(m)
								if sentCheck is not None:
									raise RuntimeError("socket connection broken, socket couldn't receive data")
							
							if filename not in times.keys():
								times[filename] = {
									"nonCached": datetime.today().timestamp() - time,
									"cached": -1
								}
							else:
								times[filename]["nonCached"] = datetime.today().timestamp() - time
								
							fileobj = open(filePath, "wb")
							fileobj.flush()
							fileobj.writelines(cmessage)
							fileobj.close()
						else:
							raise RuntimeError("socket connection broken, response message empty")
						# Fill in end.
					except (ValueError, RuntimeError, ConnectionResetError, BaseException):
						print("Illegal request")
						if ConnectionResetError:
							print("Remote Host closed connection. Response failed.")
				else:
					print("Server responded with error.")
				tcpCliSock.shutdown(1)
				tcpCliSock.close()
	except KeyboardInterrupt:
		print(json.dumps(times, sort_keys=True, indent=4))
		print('Exiting')
		exit(0)
		# TODO
