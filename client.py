#CS495 Independent Study Fall 2015 - Secure Network Communications //  Dr. Gamage
# @Southern Illinois University Edwardsville
#Brad Meyer - brameye@gmail.com
#client.py -- the clientside in a simple SMTP/TLS program
#Anyone is free to use or modify this code to fit their needs.
#Credit to Floyd Bone for helping me tidy up the code on the SMTP side and fix some bugs i encountered when i first made the SMTP in CS447



import ssl
import socket
import sys
import re
import os
import time
import pprint

domain = "@495fs15.edu"
serverHostName = socket.gethostname()


#This function just handles sending via the socket and then blocking/waiting for a response from the server
def TCPTalk(s, response):
	s.send(response)
	reply = s.recv(1024)
	return reply

#This function handles a user instance where an invalid password is being submitted.
#Error code 235 indicates password success, and the pwflag is flipped to indicate that and end the loop.
def PasswordHandler(socket, password):
	pwflag = 0
	while pwflag == 0:
		msg = TCPTalk(socket, password)
		if '235' in msg:
			pwflag = 1
		else:
			password = raw_input("Invalid Password -- Try Again\nPlease enter your password:")

#This function handles the email building on the client end
#Code 250 means success
def send(socket):
	#mailfrom
	mailFrom = user + domain
	response = "MAIL FROM: " + mailFrom
	serverReply = TCPTalk(socket, response)
	if serverReply[:3] != '250':
		print serverReply
		print "\nMail Operation Failed...aborting program...."
		sys.exit(1)
	#recp to
	#i did not implement any serious error catching here, other than to check the domain. Consider disallowing special characters for email usernames
	rcpt = raw_input("Enter the recipient's email. Please include the domain (@495fs15.edu): ")
	if "495fs15.edu" not in rcpt:
		print "Invalid Email--try again\n"
		sys.exit(1)
	response = "RCPT TO: " + rcpt
	serverReply = TCPTalk(socket, response)
	if serverReply[:3] != '250':
		print "\nMail Operation Failed...aborting program...."
		sys.exit(1)
	print "Please enter the message to be sent. Complete message entry with a '.' on a line by itself.\n"
	print 'From	: ' + mailFrom + '\n'
	print 'To	: ' + rcpt	+ '\n'
	serverReply = TCPTalk(socket, 'DATA')
	#Code 334 indicates to proceed with SMTP data transmission
	if serverReply[:3] != '334':
		print "\nMail Operation Failed, server error received. Program exiting...\n"
		sys.exit(1)
	userIn = raw_input('Subject: ')
	print'\n'
	body = 'Subject: '
	#This handles EOF for the data
	while userIn != '.':
		body = body + userIn + '\n'
		userIn = raw_input()
	serverReply = TCPTalk(socket, body)
	return

#This functin handles the email retrieval 
def retrieve(socket):
	path = user + '/'
	#create directory to dump emails
	if not os.path.exists(path):
		os.mkdir(path)
	#ask the server how many emails exist
	response = "USER " + user
	serverReply = TCPTalk(socket, response) 
	print user + ", you have " + serverReply[0] + " messages...\n"
	if serverReply[0] != '0':
		messageCount = raw_input("How many emails would you like to retieve?\n")
		#Create HTTP GET Statement
		getReq = 'GET /db/' + user + '/ HTTP/1.1\nHost: ' + serverHostName + '\nCount: ' + messageCount
		serverReply = TCPTalk(socket, getReq)
		if 'HTTP/1.1 200 OK' not in serverReply:
			print "Email retrieveal unsuccessful, please try again"
			return
		saveMail(path, int(messageCount), serverReply)
	else:
		print "\nThere are no messages available for retrieval... :(\n"
	return

#This function saves the mail received via the GET statement (retrieve function)
def saveMail(path, count, getReply):
	choice = raw_input("Enter 'y' to see the emails in this window:")
	messages = getReply.split('HTTP/1.1 200 OK')
	for i in range(1, count + 1):
		c = str(i)
		filename = c + '.txt'
		#changed mode from w to r+ for choice thing
		email = open(path + filename, 'r+')
		email.write(messages[i])
	if choice == 'y':
		for line in email:
			print line
	return


#Handles session end
def quitSession(s):
	serverReply = TCPTalk(s, 'QUIT')
	
	if serverReply[:3] == '221':
		print "Program shutting down, goodbye....\n"
	s.close()
	exit()

def main():
	smtpCommands = {
	'1' : send,
	'2' : retrieve, 
	'3' : quitSession
	}


	serverName = sys.argv[1]
	tcpPort = int(sys.argv[2])
	eDomain = "@495fs15.edu"


	print "Welcome to Brad's SMTP + TLS client program!\nEstablishing server connection....\n"
	
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#TLS BEGINS HERE!!!
	#The certs file should obviously be updated for whoever else may be using this. In my example
	#both the server and client have access to the same certs (one folder/one machine).
	#I think the path required must be the absolute path to the cert as shown below, not relative path.
	secureCS = ssl.wrap_socket(clientSocket, 
				   ca_certs='/home/brad/Documents/REPOS/TLSproject/cert.pem',
				   cert_reqs=ssl.CERT_REQUIRED,
				   ssl_version=ssl.PROTOCOL_TLSv1)

	secureCS.connect((serverName, tcpPort))
	#Server hello message
	greeting = 'HELO ' + socket.gethostname()
	global serverHostname 
	serverHostName = socket.gethostname()
	serverReply = TCPTalk(secureCS, greeting)
	#Code 220 is helo success
	if serverReply[:3] != '220':
		print "Failed to initiate SMTP connection...shutting down"
		sys.exit(0)
	
	print "Server connection initalized, waiting for secure connection...\n"
	print "Testing secure connection....\n"	
	#print some fun info about the TLS connection. Optional of course
	print repr(secureCS.getpeername())
	print secureCS.cipher()
	print pprint.pformat(secureCS.getpeercert())

	global user
	#username handling
	user = raw_input("Please enter your username\n")
	userEmail = user + eDomain

	#authentication stuff
	
	msg = 'AUTH'
	serverReply = TCPTalk(secureCS, msg)
	#protocol implementation from CS447. I think dxnlcm6hbwu6 == base64('username')?
	if '334 dXNlcm5hbWU6' not in serverReply:
		print 'Invalid AUTH Reply received....shutting down.'
		sys.exit(0)

	serverReply = TCPTalk(secureCS, userEmail)
	
	if '334 cGFzc3dvcmQ6' in serverReply:
		data = raw_input("Please enter your password\n")	
		PasswordHandler(secureCS, data)	
	elif '330' in serverReply:
		#code 330 indicates the user is new -- so a new user password was generated, attached after 330
		password = serverReply.split(" ")
		print "Welcome " + user + ", your assigned password is " + password[1] + ".\nThis program is now terminating and establishing a new server connection...\n"
		secureCS.close()
		time.sleep(3)
		main() 
	else:
		print "Invalid AUTH reply received...shutting down"
		sys.exit(0)

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
