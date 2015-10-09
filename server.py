#CS495 -- Indpt Studies Fall 2015 -- Secure Network Communications // Dr. Gamage
#Brad Meyer brameye@gmail.com
#sever.py
#The Server in a basic SMTP-TLS setup. An extension of our SMTP project from CS447 Networking
#This code can be freely modified or shared to fit your needs.

import ssl
import socket
import threading
import os
import datetime
import sys
import time


def TCP_Thread_Handler(cSocket, addr, hFlag, tFlag):
	print "Got a TCP connection!\n"
	while 1:
		msg = cSocket.recv(1024)
		if 'HELO' in msg:
			hFlag = 1
			response = "220 Hello there, old friend"
			cSocket.send(response)
		elif 'STARTTLS' in msg:
			if hFlag == 1:
				response = "STARTTLS"
				cSocket = ssl.wrap_socket(cSocket,
							server_side=True, 
						  	certfile='/home/brad/Documents/REPOS/TLSproject/cert.pem',
						  	keyfile='/home/brad/Documents/REPOS/TLSproject/cert.pem',
						  	ssl_version=ssl.PROTOCOL_TLSv1)
				tFlag = 1
				time.sleep(5)
				cSocket.send(response)
			else:
				response = "503 Bad Sequence of Commands"
				cSocket.send(response)
		elif 'EHLO' in msg:
			if tFlag == 1:
				response = "250 Secure Connection Established"
				cSocket.send(response)
			else:
				response = "503 Bad Sequence of Commands"
				cSocket.send(response)
		elif 'MAIL FROM:' in msg:
			if heloFlag == 1 and tFlag == 1:
				sender = msg.split(':')
				global mailFrom
				mailFrom = sender[1]
				response = "250 Requested Action Completed"
				cSocket.send(response)
			else:
				response = "503 Bad Sequence of Commands"		
				cSocket.send(response)
		print 'STOPPED HERE!!!'
		#STOPPED HERE!!!!
		#todo: maybe consolidate send statements to one at the end of loop




def CheckRootPath(path):
	if not os.path.exists(path):
		os.makedirs(path)
	else:
		print("Warning: Email directory ./db/ already exists. All new emails will be kept in this directory\n")
	return


def main():
	tcpPort = int(sys.argv[1])


	CheckRootPath("./db/")
	tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	#possible debug area for 2 argument, currently 1 argument(UDP port)

	
	tcpSocket.bind(('', tcpPort))
	tcpSocket.listen(10)
	print "Listening on TCP port " + str(tcpPort) + "....\n"

	heloFlag = 0
	tlsFlag = 0
	while 1:
		client, addr = tcpSocket.accept()
		thread_handler = threading.Thread(target=TCP_Thread_Handler, args=(client, addr, heloFlag, tlsFlag))
		thread_handler.start()



if __name__ == '__main__':
	main()
