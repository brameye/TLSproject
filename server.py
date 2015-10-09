#CS495 -- Indpt Studies Fall 2015 -- Secure Network Communications // Dr. Gamage
#Brad Meyer brameye@gmail.com
#sever.py
#The Server in a basic SMTP-TLS setup. An extension of our SMTP project from CS447 Networking
#This code can be freely modified or shared to fit your needs.


import socket
import thread
import os
import datetime
import sys


def TCP_Thread_Handler(cSocket, addr, flag):
	print "Got a TCP connection!\n"
	while 1:
		msg = cSocket.recv(1024)
		if 'HELO' in msg:
			flag = 1
			#LEFT OFF HERE!!!!!!!
			response
	




def CheckRootPath(path):
	if not os.path.exists(path):
		os.makedirs(path)
	else:
		print("Warning: Email directory ./db/ already exists. All new emails will be kept in this directory\n")
	return


def main():
	tcpPort = int(sys.argv[1])


	CheckRootPath("./db/")
	serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	#possible debug area for 2 argument, currently 1 argument(UDP port)

	
	tcpSocket.bind(('', tcpPort))
	tcpSocket.listen(10)
	print "Listening on TCP port " + tcpPort + "....\n"

	heloFlag = 0

	while 1:
		client, addr = TCPSocket.accept()
		thread_handler = threading.Thread(target=TCP_Thread_Handler, args=(client, addr, heloFlag))
		thread_handler.start()



if __name__ == '__main__':
	main()
