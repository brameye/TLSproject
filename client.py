#CS495 Independent Study Fall 2015 - Secure Network Communications 
# @Southern Illinois University Edwardsville
#Brad Meyer - brameye@gmail.com
#client.py -- the clientside in a simple SMTP/TLS program
#Anyone is free to use or modify this code to fit their needs.
#Credit to Floyd Bone for helping me tidy up the code on the SMTP side and fix some bugs i encountered when i first made the SMTP in CS447




import socket
import sys
import re
import os
import time

user = "null"


def TCPTalk(s, response):
	s.send(response)
	reply = s.recv(1024)
	return reply

def send(socket, mailFrom):
	#mailfrom
	response = "MAIL FROM " + mailFrom
	serverReply = TCPTalk(socket, response)
	if serverReply[:3] != '250':
		print serverReply
		print "\nMail Operation Failed...aborting program...."
		sys.exit(1)
	#recp to
	#i did not implement any error catching here
	rcpt = raw_input("Enter the recipient's email. Please include the domain (@495fs15.edu): ")
	if "495fs15.edu" not in rcpt:
		print "Invalid Email--try again\n"
		sys.exit(1)
		#while 1: THIS IS FOR ERROR CHECKING (if i implement it)
	
	response = "RCPT TO " + rcpt
	serverReply = TCPTalk(socket, response)
	if serverReply[:3] != '250':
		print "\nMail Operation Failed...aborting program...."
		sys.exit(1)
	print "Please enter the message to be sent. Complete message entry with a '.' on a line by itself.\n"
	print 'From	: ' + mailFrom + '\n'
	print 'To	: ' + rcpt	+ '\n'
	serverReply = TCPTalk(socket, 'DATA')	
	if serverReply[:3] != '250':
		print "\nMail Operation Failed, server error received. Program exiting...\n"
		sys.exit(1)
	userIn = rawinput('Subject: ')
	print'\n'
	body = 'Subject: '

	while userIn != '.':
		body = body + userIn + '\n'
		userIn = raw_input()
	serverReply = TCPTalk(socket, body)
	return


def retrieve(socket):
	path = user + '/'
	if not os.path.exists(path):
		os.mkdir(path)
		
	response = "USER " + user
	serverReply = TCPTalk(socket, response) 
	print user + ", you have " + serverReply[0] + " messages...\n"
	if serverReply[0] != '0':
		messageCount = raw_input("How many emails would you like to retieve?\n")
		getReq = 'GET /db/' + user + '/ HTTP/1.1\nHost: ' + serverHostname + '\nCount: ' + messageCount
		serverReply = TCPTalk(socket, getReq)
		if 'HTTP/1.1 200 OK' not in serverReply[0]:
			print "Email retrieveal unsuccessful, please try again"
			return
		saveMail(path, int(messageCount), serverReply[0])
	else:
		print "\nThere are no messages available for retrieveal... :(\n"
	return

def saveMail(path, count, getReply):
	messages = getReply.split('HTTP/1.1 200 OK')
	for i in range(1, count + 1):
		c = str(i)
		filename = c + '.txt'
		email = open(path + filename, 'w')
		email.write(messages[i])
	return



def quitSession(s):
	serverReply = TCPTalk(s, 'QUIT')
	if serverReply[:3] == '221':
		print "Program shutting down, goodbye....\n"
	exit()

def main():
	smtpCommands = {
	'1' : send,
	'2' : retrieve, 
	'3' : quitSession
	}


	serverName = sys.argv[1]
	tcpPort = int(sys.argv[2])
	#possibly remove UDP?
	#udpPort = sys.argv[3]
	eDomain = "@495fs15.edu"


	print "Welcome to Brad's SMTP + TLS client program!\nEstablishing server connection....\n"
	
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientSocket.connect((serverName, tcpPort))
	
	greeting = 'HELO ' + socket.gethostname()
	global serverHostname 
	serverHostName = socket.gethostname()
	serverReply = TCPTalk(clientSocket, greeting)


	if serverReply[:3] != '220':
		print "Failed to initiate SMTP connection...shutting down"
		sys.exit(0)
	
	print "Server connection initalized, waiting for secure connection...\n"

	#tell the server that we want TCP TLS

	msg = "STARTTLS"
	serverReply = TCPTalk(clientSocket, msg)
	
	if serverReply[:8] != "STARTTLS":
		print "Error establishing secure SMTP connection...shutting down"
	
	#create new secure connection

	secureCS = ssl.wrap_socket(clientSocket, 
				   ca_certs='cert.pem',
				   cert_reqs=ssl.CERT_REQUIRED,
				   ssl_version=ssl.PROTOCOL_TLSv1)

	global user

	user = raw_input("Please enter your username\n")
	#global user
	#user = username
	userEmail = user + eDomain

	while 1:
		print userEmail + "495fs15 SSMTP Options\n--------------------"
		print "(1) Send an email\n(2) Retrieve your Emails\n(3) Quit\n"
		choice = raw_input("Please enter either 1, 2, or 3:  \n")
		if choice in smtpCommands:
			smtpCommands[choice](secureCS)
		else:
			print "Invalid option, please try again...\n"
		
	sys.exit(0)

if __name__ == '__main__':
	main()
