#CS495 Independent Study Fall 2015 - Secure Network Communications 
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

#user = "null"
domain = "@495fs15.edu"
serverHostName = socket.gethostname()


def TCPTalk(s, response):
	s.send(response)
	reply = s.recv(1024)
	return reply

def PasswordHandler(socket, password):
	pwflag = 0
	while pwflag == 0:
		msg = TCPTalk(socket, password)
		#DEBUG STATEMENT
		print msg
		if '235' in msg:
			pwflag = 1
		else:
			password = raw_input("Invalid Password -- Try Again\nPlease enter your password:")
	
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
	#i did not implement any error catching here
	rcpt = raw_input("Enter the recipient's email. Please include the domain (@495fs15.edu): ")
	if "495fs15.edu" not in rcpt:
		print "Invalid Email--try again\n"
		sys.exit(1)
		#while 1: THIS IS FOR ERROR CHECKING (if i implement it)
	print '2'
	response = "RCPT TO: " + rcpt
	serverReply = TCPTalk(socket, response)
	#DEBUG STATEMENT
	print '1'
	print serverReply
	if serverReply[:3] != '250':
		print "\nMail Operation Failed...aborting program...."
		sys.exit(1)
	print "Please enter the message to be sent. Complete message entry with a '.' on a line by itself.\n"
	print 'From	: ' + mailFrom + '\n'
	print 'To	: ' + rcpt	+ '\n'
	serverReply = TCPTalk(socket, 'DATA')
	#DEBUG STATEMENT
	print serverReply	
	if serverReply[:3] != '334':
		print "\nMail Operation Failed, server error received. Program exiting...\n"
		sys.exit(1)
	userIn = raw_input('Subject: ')
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
		getReq = 'GET /db/' + user + '/ HTTP/1.1\nHost: ' + serverHostName + '\nCount: ' + messageCount
		serverReply = TCPTalk(socket, getReq)
		#NOTE: REMOVD '[0]' from serverReply's betlow this statement
		if 'HTTP/1.1 200 OK' not in serverReply:
			#DEBUG STATEMENT
			print serverReply
			print serverReply[0]
			print "Email retrieveal unsuccessful, please try again"
			return
		saveMail(path, int(messageCount), serverReply)
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

	secureCS = ssl.wrap_socket(clientSocket, 
				   ca_certs='/home/brad/Documents/REPOS/TLSproject/cert.pem',
				   cert_reqs=ssl.CERT_REQUIRED,
				   ssl_version=ssl.PROTOCOL_TLSv1)

	secureCS.connect((serverName, tcpPort))
	
	greeting = 'HELO ' + socket.gethostname()
	global serverHostname 
	serverHostName = socket.gethostname()
	serverReply = TCPTalk(secureCS, greeting)

	if serverReply[:3] != '220':
		print "Failed to initiate SMTP connection...shutting down"
		sys.exit(0)
	
	print "Server connection initalized, waiting for secure connection...\n"
	#print "Testing secure connection....\n"	

	global user

	user = raw_input("Please enter your username\n")
	userEmail = user + eDomain

	#authentication stuff
	
	msg = 'AUTH'
	serverReply = TCPTalk(secureCS, msg)
	
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
