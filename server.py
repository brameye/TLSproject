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

serverHostName = socket.gethostname()

def TCP_Thread_Handler(cSocket, addr, heloFlag, tFlag):
	cSocket = ssl.wrap_socket(cSocket,
				server_side=True, 
				certfile='/home/brad/Documents/REPOS/TLSproject/cert.pem',
				keyfile='/home/brad/Documents/REPOS/TLSproject/cert.pem',
				ssl_version=ssl.PROTOCOL_TLSv1)
	print "Got a TCP connection!\n"
	while 1:
		msg = cSocket.recv(1024)
		if 'HELO' in msg:
			heloFlag = 1
			response = "220 Hello there, old friend"
		elif 'USER' in msg:
			user = msg.split(' ')
			path = 'db/' + user[1] + '/'
			response = str(countFiles(path))
		elif 'GET' in msg:
			m1 = msg.split('/')
			m2 = msg.split(':')
			u = m1[2]
			path = 'db/' + user[1] + '/'
			count = int(m2[2])
			response = getEmail(path, count)
		elif 'MAIL FROM:' in msg:
			if heloFlag == 1:
				sender = msg.split(':')
				global mailFrom
				mailFrom = sender[1]
				print mailFrom
				response = "250 Requested Action Completed"
			else:
				response = "503 Bad Sequence of Commands"		
		elif 'RCPT TO:' in msg:
			if heloFlag == 1:
				global rcptTo
				response = "250 Requested Action Completed"
				begin = msg.find(':') + 2
				rcptTo = msg[begin:]
				end = msg.find('@', begin)
				path = 'db/' + msg[begin:end]
				if not os.path.exists(path): 
					os.mkdir(path)
			else:
				response = '503 Bad Sequence of Commands'
		elif 'DATA' in msg:
			if heloFlag == 1:
				response = '334 Please Enter Data'
			else:
				response = '503 Bad Sequence of Commands'
		elif 'Subject' in msg:
			response = '250 Requested Mail Action Completed'
			CreateEmail(msg)
		elif 'QUIT' in msg:
			if heloFlag == 1:
				response = '221 SMTP Channel shutting down...'
				
			else:
				response = '503 Bad Sequence of Commands'
		else:
			response = '500 Syntax Error -- command unrecognized'

		cSocket.send(response)
		

def CreateEmail(msg):
	t = timeStamp()
	rcpt = rcptTo.split('@')
	path = ('db/' + rcpt[0] + '/')
	fileCount = countFiles(path) + 1
	pre = str(fileCount).zfill(3)
	filename = pre + '.email'
	data = 'Date: ' + t + '\n' + 'From: ' + mailFrom + '\n' + 'To: ' + rcptTo + '\n'
	data = data + msg
	email = open(path + filename, 'w')
	email.write(data)
	email.close()
	#debug statement
	print data	
	return

def getEmail(path, count):
	files = os.listdir(path)
	now = timeStamp()
	c = str(count)
	emails = ''
	for i in range(count):
		msg = str(i+1)
		data = 'HTTP/1.1 200 OK \nServer: ' + serverHostName + '\nLast-Modified ' + now + '\nCount: ' + c + '\nContent Type: text/plain\nMessage: ' + msg + '\n'
		email = open(path + files[i], 'r')
		e = email.read()
		data = data + e
		emails = emails + data
		email.close()
	return emails


def timeStamp():
	ts = str(datetime.datetime.now().strftime("%A, %d, %B %Y %I:%M%p"))
	return ts

def countFiles(path):
	num = len([e for e in os.walk(path).next()[2] if e[-6:] == '.email'])
	return num


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
