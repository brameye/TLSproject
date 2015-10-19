#CS495 -- Indpt Studies Fall 2015 -- Secure Network Communications // Dr. Gamage
#Brad Meyer brameye@gmail.com
#sever.py
#The Server in a basic SMTP-TLS setup. An extension of our SMTP project from CS447 Networking
#Credit to F. Bone from CS447 who didn't mind helping me fix some small bugs i had on the SMTP stuff.
#This code can be freely modified or shared to fit your needs.



import ssl
import socket
import threading
import os
import datetime
import time
import sys
from random import randint
import pprint

serverHostName = socket.gethostname()
userFile = "./.user_pass"

#This is where threads go to live a happy, fulfilling life as a protocol handler. Eventually they die and are forgotten forever! Yay!
def TCP_Thread_Handler(cSocket, addr, heloFlag, tFlag):
	cSocket = ssl.wrap_socket(cSocket,
				server_side=True, 
				certfile='/home/brad/Documents/REPOS/TLSproject/cert.pem',
				keyfile='/home/brad/Documents/REPOS/TLSproject/cert.pem',
				ssl_version=ssl.PROTOCOL_TLSv1)
	print "\n ---------------COOL TLS INFORMATION------------------"
	print repr(cSocket.getpeername())
	print cSocket.cipher()
	print pprint.pformat(cSocket.getpeercert())
	print "-------------------------------------------------------"

	print "Got a TCP connection!\n"
	authFlag = 0
	while 1:
		msg = cSocket.recv(1024)
		if 'HELO' in msg:
			heloFlag = 1
			response = "220 Hello there, old friend"
			Write_Log_Entry(addr, "220", "HELO", "Connected created")
		elif 'AUTH' in msg:
			Write_Log_Entry(addr, "334d", "AUTH", "Auth initalized")
			cSocket.send('334 dXNlcm5hbWU6') #this message indicates to go ahead with AUTH sequence
			msg = cSocket.recv(1024)
			user = msg
			result = LookupUser(user) #user lookup to see if new or not
			if '334' in result:
				Write_Log_Entry(addr, "334c", "AUTH", "Existing Username Located")
				cSocket.send(result)
				pw = cSocket.recv(1024)
				response = HandleAuthentication(user, pw) #handles user authentication if nto new
				while '535' in response:
					Write_Log_Entry(addr, "535", "AUTH", "Bad Password supplied")
					cSocket.send(response)
					pw = cSocket.recv(1024)
					response = HandleAuthentication(user, pw)
				authFlag = 1
			elif '330' in result:
				#code 330 indicates new user, so we generate a pass, store it, send it to the user and open a new connection
				newPass = NewUserRegistration(user)
				Write_Log_Entry(addr, "330", "AUTH", "New user created")			
				response = "330 " + str(newPass)
				cSocket.send(response)
				cSocket.close()	
				break		
		elif 'USER' in msg: 
			if authFlag == 1:
				user = msg.split(' ')
				path = 'db/' + user[1] + '/'
				response = str(countFiles(path)) # this response returns the number of emails available to a user
		elif 'GET' in msg:
			if heloFlag == 1 and authFlag == 1:
				m1 = msg.split('/')
				m2 = msg.split(':')
				u = m1[2]
				path = 'db/' + user[1] + '/'
				count = int(m2[2])
				response = getEmail(path, count)
			else:
				response = "503 Bad Sequence of Commands"
		elif 'MAIL FROM:' in msg:
			if heloFlag == 1 and authFlag == 1:
				sender = msg.split(':')
				global mailFrom
				mailFrom = sender[1]
				print mailFrom
				response = "250 Requested Action Completed"
			else:
				response = "503 Bad Sequence of Commands"		
		elif 'RCPT TO:' in msg:
			if heloFlag == 1 and authFlag == 1:
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
			Write_Log_Entry(addr, "250", "MAIL", "MAIL Sequence initiated")
			response = '250 Requested Mail Action Completed'
			CreateEmail(msg)
		elif 'QUIT' in msg:
			response = '221 SMTP Channel shutting down...'

		else:
			response = '500 Syntax Error -- command unrecognized'

		if '330' not in response:
			cSocket.send(response)
		if '221' in response:
			cSocket.close()
			break


def NewUserRegistration(user):
	#this line generates a 5-digit random number sequence to be used as the password for new users
	pw = int(''.join(["%s" % randint(0, 9) for num in range(0,5)]))
	#the next lines encode the password + 495 (course number) into base64
	#and then write the to the userfile "user pass"
	encodePW = str(pw + 495).encode('base64', 'strict')
	filename = "./.user_pass"
	file = open(filename, 'a')
	file.write(user + " " + encodePW + "\n")
	return pw


def LookupUser(user):
	msg = '330'
	name = user.split("@")
	searchfile = open("./.user_pass", "r")
	for entry in searchfile:
		if name[0] in entry:
			msg = '334 cGFzc3dvcmQ6'
		#print "no user entry found! creating new user..."
		#DEBUG PRINT
	return msg


def HandleAuthentication(username, password):
	if not AnInt(password):
		#DEBUG STATEMENT
		print 'No match found!'
		return '535'
	#adds the pw salt
	password = int(password) + 495
	encodePW = str(password).encode('base64', 'strict') #encodes password with base64
	file = open(userFile, 'r') #this searches the user file for a matching user+pass sequence
	for line in file:
		data = line.split(" ")
		if str(data[0]) == str(username):
			if str(data[1]) == str(encodePW):
				return '235'
	return '535'

#function to determine if X is an integer
def AnInt(x):
	try:
		int(x)
		return True
	except ValueError:
		return False


def Write_Log_Entry(destIP, protocol_cmd, message_code, desc):
	t = time.strftime("%c")
	log = t + " " + str(socket.gethostbyname(socket.gethostname()) + " " + str(destIP[0]) + " " + str(protocol_cmd) + " " + str(message_code) + " " + desc + "\n")
	path = "./.TLSServer_log"
	file = open(path, 'a')
	file.write(log)


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

#just counts the files within a directory
def countFiles(path):
	if not os.path.exists(path):
		return 0
	num = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])	
	return num

#creates the database, if not already created
def CheckRootPath(path):
	if not os.path.exists(path):
		os.makedirs(path)
	else:
		print("Warning: Email directory ./db/ already exists. All new emails will be kept in this directory\n")
	return


def main():
	tcpPort = int(sys.argv[1])

	if not os.path.exists("./.user_pass"):
		file("./.user_pass", 'w').close()
		print "Creating user DB..."
	CheckRootPath("./db/")
	tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	
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
