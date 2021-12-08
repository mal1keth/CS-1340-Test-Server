import socket 
import json
import random

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

IP = '127.0.0.2'
PORT = 5545

serverSocket.bind( (IP, PORT))


serverSocket.listen(1)


print("Server is listening at: ", IP, PORT)
print()


# -----  Data ------

credParam = {}
seenIP = [ ]
votes = {"A" : 0, "B": 0, "C": 0}
passPool = []
welcString = 'Welcome! You can participate in the vote by presenting your password. Reply with a ”1” if you want to participate now; with a ”2” if you want to see the results; and with ”3” other wise.'

def genPass(n):
	global passPool
	p = ""
	for i in range(n):
		p+= chr(random.randint(33,126))
	if p in passPool:
		p = genPass(n)
	else:
		passPool.append(p)
	return p


def handleVoting(clientSocket, ip, voted):
	global credParam
	global votes
	if voted==1:
		clientSocket.send("You have already voted (-1)".encode())
		return
	else:
		clientSocket.send("Logged in successfully. Press 1 to vote for A, 2 for B, and 3 for C (0)".encode())
		choice = clientSocket.recv(1024).decode()
		if choice == '1':
			votes['A']+=1
		elif choice == '2':
			votes['B']+=1
		elif choice == '3':
			votes['C']+=1
		else:
			clientSocket.send("Erroneous Input (-1)".encode())
			return
		p = genPass(8)
		credParam[ip]["pass2"] = p
		credParam[ip]["voted"] = 1
		clientSocket.send( ("Vote registered successfully. Your password for viewing votes is: "+p+" (1)").encode())
		return

def handleEmail(email):
	req = "@ashoka.edu.in"
	if(len(email) <= len(req)):
		return -1
	elif( email[ len(email)-len(req) : len(email) ] != req):
		return -1
	return 1

def handleClient(clientSocket, addr):
	global seenIP
	global credParam
	global votes
	# -------------- HandShake ----------------
	print("Connection Established: ", addr)
	clientSocket.send("Connected\n".encode())
	handShake = clientSocket.recv(1024).decode()
	if(handShake != "Handshake"):
		print("Something went wrong. Disconnecting from Client.")
		return
	ip = addr[0]
	# ----- Welcome String and Receiving Input -----
	clientSocket.send( (welcString + " (0)" ).encode())
	choice = (clientSocket.recv(1024).decode())

	# -------------- Choice Selection ---------------
	if choice== '3':
		clientSocket.send("Thank you for joining :) (1)".encode())
		return

	elif choice == '1':
		if (ip in seenIP):
			password = credParam[ip]["pass1"]
			voted = credParam[ip]["voted"]
			clientSocket.send("Please enter password for voting: (0)".encode())
			recPass = clientSocket.recv(1024).decode()
			if password == recPass:
				handleVoting(clientSocket, ip, voted)
			else:
				clientSocket.send("Incorrect Password (-1)".encode())
		else:
			clientSocket.send("Please enter Ashoka Email ID:  (0)".encode())
			email = clientSocket.recv(1024).decode()
			if (handleEmail(email) == -1):
				clientSocket.send("Only Ashoka users are allowed to vote. (-1)".encode())
			else: 
				seenIP.append(ip)
				p = genPass(8)
				credParam[ip] = { "email": email, "pass1": p, "pass2": None, "voted": 0}
				clientSocket.send(("You have been registered successfully, your password is: "+p+"\nWould you like to continue voting? (y/n) (0)").encode() )
				choice = clientSocket.recv(1024).decode()

				if choice == 'y' or choice == 'Y':
					handleVoting(clientSocket, ip, 0)
				elif choice == 'n' or choice == 'N':
					clientSocket.send("Thanks for registering.  (1)".encode())
				else:
					clientSocket.send("Erroneous Input.(-1)".encode())

	elif choice == '2':
		if(not (ip in seenIP) or not(credParam[ip]["voted"]==1) ):
			clientSocket.send("You have not voted yet, you can't see voting results.(-1)".encode())
		else:
			p2 = credParam[ip]["pass2"]
			v = credParam[ip]["voted"]
			clientSocket.send("Please enter password for viewing votes:  (0)".encode())
			p = clientSocket.recv(1024).decode()
			if p == p2:
				data = json.dumps(votes)+ " (3)"
				clientSocket.send(data.encode())
			else:
				clientSocket.send("Password is incorrect.(-1)".encode())
	else:
		clientSocket.send("Erroneous Input.(-1)".encode())
	print("Disconnecting from client.")

while True:
	(clientSocket, addr) = serverSocket.accept()
	handleClient(clientSocket, addr)
	clientSocket.close()

print("Server is going offline")
serverSocket.close()

'''

Sequence of Events:

1. Server Listens on Port 5545
2. Client Connects
3. Server sends connection message
4. Client acknowledges with Handshake
5. Server sends Welcome String
6. Client Responds with Choice
7. Case '1': 
			a. If IP is present in SeenIP-
				i. Ask client for password
				ii. Client sends password
				iii. Server checks password
					1. If correct check if Client has voted
						a. If yes, then-
							i. Server sends "You have already voted"
							ii.Client Receives
					 	b.If no then-
							i. Stringify voting candidates using json and send to client
							ii. Client Receives
							iii. Client sends vote
							iv. Server receives and registers it, sets client's vote to 1
							v. Server generates password and sends to client to view votes
							vi. Client receives
					2. If incorrect-
						a. Server sends "Incorrect Password"
						b. Client Receives
				iv. Connection Closes

			b. If IP is not present in SeenIP-
				i. Ask client for email address
				ii. Client sends email address.
				iii. Server generates password and sends to client
8. Case '2' follows similarly
9. Case '3'
		a. Server sends message
		b. Client accepts
10. Else:
		a. Server informs client of erroneous input and disconnects
'''
